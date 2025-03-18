import asyncio
from multiprocessing import Queue, Barrier
from random import randint
from time import time
from typing import Optional

from web3 import WebSocketProvider
from web3.middleware import ExtraDataToPOAMiddleware
from web3 import AsyncWeb3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.Benchmark import Benchmark

class Worker:
    def __init__(
        self,
        benchmark: 'Benchmark',
        barrier: Barrier,  # type: ignore
        log_queue: Queue,
        i: int,
        worker_args: Optional[dict],
    ) -> None:
        self.benchmark = benchmark
        self.barrier = barrier
        self.log_queue = log_queue
        self.i = i
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
