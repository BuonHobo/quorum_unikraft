import asyncio
from provisioner.benchmark.Benchmark import Benchmark
from provisioner.quorum.Quorum import Quorum


class Experiment:
    def __init__(self, jsondata: dict) -> None:
        self.quorum = Quorum(jsondata["quorum"])
        self.benchmark: Benchmark = Benchmark(jsondata["benchmark"], self.quorum)

    async def start_quorum(self) -> None:
        print("Stopping previous quorum setups")
        await self.quorum.stop()
        print("Initializing new quorum setup")
        await self.quorum.initialize()
        print("Starting quorum")
        await self.quorum.start()
        print("Quorum started")
        await asyncio.sleep(1)
        print("Deploying contract")
        await self.quorum.deploy_contract()
        print("Contract deployed")
        await asyncio.sleep(1)

    async def restart_quorum(self) -> None:
        print("Restarting quorum")
        await self.quorum.restart()
        print("Quorum restarted")
        await asyncio.sleep(1)
        print("Deploying contract")
        await self.quorum.deploy_contract()
        print("Contract deployed")
        await asyncio.sleep(1)

    def run(self) -> None:
        asyncio.run(self.start_quorum())
        asyncio.run(self.restart_quorum())
        print("Starting benchmark")
        self.benchmark.start()
        print("Benchmark finished")