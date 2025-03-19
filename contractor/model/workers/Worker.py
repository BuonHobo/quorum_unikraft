import asyncio
from multiprocessing import Process, Queue, Barrier
from random import randint
from time import time

from web3 import WebSocketProvider
from web3.middleware import ExtraDataToPOAMiddleware
from web3 import AsyncWeb3
from typing import TYPE_CHECKING

from model.workers.WorkerStrategy import WorkerStrategy

if TYPE_CHECKING:
    from model.Benchmark import Benchmark


class Worker:
    def __init__(
        self,
        benchmark: "Benchmark",
        barrier: Barrier,  # type: ignore
        log_queue: Queue,
        i: int,
        strategy: WorkerStrategy,
    ) -> None:
        self.benchmark = benchmark
        self.barrier = barrier
        self.log_queue = log_queue
        self.i = i
        self.connectors: list[AsyncWeb3] = None  # type: ignore
        self.strategy = strategy

    @classmethod
    def get_pool(
        cls,
        benchmark: "Benchmark",
        log_queue: Queue,
        workers: int,
        strategy: WorkerStrategy,
    ):
        barrier = Barrier(workers)
        return [
            Process(target=cls(benchmark, barrier, log_queue, i, strategy).run)
            for i in range(workers)
        ]

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
                g.create_task(self.transaction(connector, nonce, host))
                nonce += 1
                await asyncio.sleep(1 / self.benchmark.rps * self.benchmark.processes)

    async def main(self):
        await self.setup_connectors()
        await self.strategy.prepare_worker(self)
        await self.bench()
        await self.disconnect()

    async def transaction(self, connector, nonce, host):
        send = -1
        rcpt = -1
        start = time()
        try:
            tx_hash = await self.strategy.send_transaction(connector, nonce, self.i)
            send = time()
            await connector.eth.wait_for_transaction_receipt(
                tx_hash, timeout=self.benchmark.timeout
            )
            rcpt = time()
        except Exception as e:
            print(f"Exception in pid {self.i} on host {host}: {e}")
        finally:
            self.log_queue.put((self.i, host, nonce, start, send, rcpt))

    async def prepare_transaction(self, connector, nonce, **kwargs):
        raise NotImplementedError("This method should be implemented by subclasses.")
