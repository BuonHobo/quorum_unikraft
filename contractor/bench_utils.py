from __future__ import annotations
import asyncio
from multiprocessing import Barrier, Process, Queue
from pathlib import Path
from random import choice, randint
import signal
from time import sleep, time
from typing import Optional, override

from hexbytes import HexBytes
from web3 import AsyncWeb3, WebSocketProvider
from eth_account.signers.local import LocalAccount
from web3.middleware import ExtraDataToPOAMiddleware
from web3.contract import AsyncContract


class Benchmark:
    def __init__(
        self,
        hosts: list[str],
        rps: int,
        duration: int,
        output_file: Path,
        processes: int,
        timeout: int,
        worker: type[Worker],
        worker_args: dict,
    ) -> None:
        self.hosts = hosts
        self.rps = rps
        self.duration = duration
        self.output_file = output_file
        self.processes = processes
        self.timeout = timeout
        self.log_queue = Queue()
        self.worker = worker
        self.worker_args = worker_args

    def start(self):
        log_queue = Queue()
        logger = Process(
            target=Logger(self, log_queue).run,
        )
        logger.start()

        barrier = Barrier(self.processes)
        subprocesses = [
            Process(
                target=self.worker(self, barrier, log_queue, i, self.worker_args).run
            )
            for i in range(self.processes)
        ]
        for process in subprocesses:
            process.start()
        for process in subprocesses:
            process.join()

        sleep(1)
        logger.terminate()


class Worker:
    def __init__(
        self,
        benchmark: Benchmark,
        barrier: Barrier,  # type: ignore
        log_queue: Queue,
        i: int,
        worker_args: Optional[dict],
    ) -> None:
        self.benchmark = benchmark
        self.barrier = barrier
        self.log_queue = log_queue
        self.i = i
        self.account: LocalAccount = None  # type: ignore
        self.connectors: list[AsyncWeb3] = None  # type: ignore
        self.worker_args = worker_args

    def run(self):
        asyncio.run(self.main())

    @staticmethod
    async def initialize_connector(connector):
        await connector.provider.connect()
        connector.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        connector.eth.default_account = (await connector.eth.accounts)[0]

    async def setup_connectors(self):
        self.connectors = [
            AsyncWeb3(WebSocketProvider(host)) for host in self.benchmark.hosts
        ]
        await asyncio.gather(
            *[self.initialize_connector(connector) for connector in self.connectors]
        )

    async def setup_account(self):
        self.account = choice(self.connectors).eth.account.create()
        pass

    async def prepare(self):
        pass

    async def disconnect(self):
        await asyncio.gather(
            *[connector.provider.disconnect() for connector in self.connectors]
        )

    async def bench(self):
        nonce = 0
        async with asyncio.TaskGroup() as g:
            offset = 1 / self.benchmark.rps * self.i
            self.barrier.wait()
            await asyncio.sleep(offset)
            t_start = time()
            while time() - t_start < self.benchmark.duration + offset:
                host = randint(0, len(self.benchmark.hosts) - 1)
                connector = self.connectors[host]
                g.create_task(self.transaction(connector, nonce, self.i, host))
                nonce += 1
                await asyncio.sleep(1 / self.benchmark.rps * self.benchmark.processes)

    async def main(self):
        await self.setup_connectors()
        await self.setup_account()
        await self.prepare()
        await self.bench()
        await self.disconnect()

    async def transaction(self, connector, nonce, pid, host):
        send = -1
        rcpt = -1
        start = time()
        try:
            signed_tx = await self.prepare_transaction(connector, nonce)
            tx_hash = await connector.eth.send_raw_transaction(
                signed_tx.raw_transaction
            )
            send = time()
            await connector.eth.wait_for_transaction_receipt(
                tx_hash, timeout=self.benchmark.timeout
            )
            rcpt = time()
        except Exception as e:
            print(f"Exception in pid {pid} on host {host}: {e}")
        finally:
            self.log_queue.put((pid, host, nonce, start, send, rcpt))

    async def prepare_transaction(self, connector, nonce, **kwargs):
        raise NotImplementedError("This method should be implemented by subclasses.")


class Logger:
    def __init__(
        self,
        benchmark: Benchmark,
        log_queue: Queue,
    ) -> None:
        self.benchmark = benchmark
        self.log_queue = log_queue

    def run(self):
        start_time = time()
        signal.signal(signal.SIGTERM, handler=lambda x, y: exit(0))
        id = 0
        with self.benchmark.output_file.open("w") as f:
            f.write("id,pid,host,nonce,sent_time,time_to_send,time_to_rcpt,recv_time\n")
            while True:
                pid, host, nonce, start, send, rcpt = self.log_queue.get()
                f.write(
                    f"{id},{pid},{host},{nonce},{start - start_time:.3f},{send - start:.3f},{rcpt - send:.3f},{rcpt - start_time:.3f}\n"
                )
                f.flush()
                id += 1


class ContractWorker(Worker):
    @override
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.contract: AsyncContract = None  # type: ignore

    @override
    async def prepare(self):
        self.contract = choice(self.connectors).eth.contract(
            address=self.worker_args["contract_address"],  # type: ignore
            abi=self.worker_args["contract_abi"],  # type: ignore
        )

    @override
    async def prepare_transaction(self, connector, nonce, **kwargs) -> HexBytes:
        tx = await self.contract.functions.proposeNewValues(
            ["P0"], [nonce]
        ).build_transaction(
            {
                "nonce": nonce,
                "gas": 25_000_000,
                "gasPrice": 0,
                "chainId": 1337,
            }  # type: ignore
        )
        return connector.eth.account.sign_transaction(tx, self.account.key)


class MoneyWorker(Worker):
    @staticmethod
    async def fund_address(connector, address, amount):
        tx_hash = await connector.eth.send_transaction(
            {
                "from": connector.eth.default_account,
                "to": address,
                "value": amount,
                "gas": 25_000_000,
                "gasPrice": 0,
                "chainId": 1337,
            }  # type: ignore
        )
        await connector.eth.wait_for_transaction_receipt(tx_hash)

    @override
    async def prepare(self):
        await self.fund_address(
            choice(self.connectors),
            self.account.address,
            self.benchmark.duration * self.benchmark.rps * 2,
        )

    @override
    async def prepare_transaction(self, connector, nonce, **kwargs) -> HexBytes:
        tx = {
            "from": self.account.address,
            "to": connector.eth.default_account,
            "value": 1,
            "nonce": nonce,
            "gas": 25_000_000,
            "gasPrice": 0,
            "chainId": 1337,
        }  # type: ignore
        return connector.eth.account.sign_transaction(tx, self.account.key)
