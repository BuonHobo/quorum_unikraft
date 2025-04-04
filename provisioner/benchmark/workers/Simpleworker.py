import asyncio
from random import randint
from time import time
from typing import override

from web3 import WebSocketProvider
from web3 import AsyncWeb3

from provisioner.benchmark.workers.Worker import Worker


class Simpleworker(Worker):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if self.i >= len(self.benchmark.hosts):
            raise ValueError(
                f"Worker {self.i} exceeds the number of hosts {len(self.benchmark.hosts)}"
            )

    @override
    async def setup_connectors(self):
        residue = len(self.benchmark.hosts) % self.benchmark.processes
        start = 0
        for i in range(self.i):
            chunk = len(self.benchmark.hosts) // self.benchmark.processes
            if i < residue:
                chunk += 1
            start += chunk
        chunk = len(self.benchmark.hosts) // self.benchmark.processes
        if self.i < residue:
            chunk += 1
        end = start + chunk
        print(f"Worker {self.i} will use hosts {start}:{end}")
        self.connectors = [
            AsyncWeb3(WebSocketProvider(self.benchmark.hosts[i]))
            for i in range(start, end)
        ]

        await asyncio.gather(
            *[self.initialize_connector(connector) for connector in self.connectors]
        )

    @override
    async def bench(self):
        nonce = 0
        async with asyncio.TaskGroup() as g:
            my_rps = self.benchmark.rps / len(self.benchmark.hosts) * len(self.connectors)
            print(f"Worker {self.i} will use {my_rps} rps")
            offset = 1 / self.benchmark.rps * self.i
            self.barrier.wait()
            await asyncio.sleep(offset)
            t_start = time()
            while time() - t_start < self.benchmark.duration + offset:
                host = randint(0,len(self.connectors)-1)
                connector = self.connectors[host]
                g.create_task(self.transaction(connector, nonce, host))
                nonce += 1
                await asyncio.sleep(1 / my_rps)