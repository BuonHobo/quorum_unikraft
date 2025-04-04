import asyncio
import importlib
from pathlib import Path
from provisioner.benchmark.Benchmark import Benchmark
from provisioner.benchmark.strategies.WorkerStrategy import WorkerStrategy
from provisioner.quorum.Quorum import Quorum


class BenchmarkScheduler:
    def __init__(self, quorum: Quorum, jsondata: dict) -> None:
        self.quorum = quorum
        self.name = jsondata["name"]
        self.output_dir = Path(jsondata["output_directory"])
        self.tx_rates = jsondata["tx_rates"]
        self.duration = jsondata["duration"]
        self.timeout = jsondata["timeout"]
        self.processes = jsondata["processes"]
        self.attempts = jsondata["attempts"]
        self.worker = self.get_worker_type(jsondata)
        self.strategies = [
            WorkerStrategy.get_strategy(data, quorum) for data in jsondata["strategies"]
        ]

    def start(self) -> None:
        for strategy in self.strategies:
            for tx_rate in self.tx_rates:
                for attempt in range(self.attempts):
                    name = f"{self.name}-{self.quorum.get_consensus()}-{strategy.get_name()}_{tx_rate}_{attempt}"
                    print(f"Setting up deployment {name}")
                    asyncio.run(self.quorum.restart())
                    benchmark = Benchmark(
                        duration=self.duration,
                        timeout=self.timeout,
                        processes=self.processes,
                        output_file=self.output_dir / f"{name}.csv",
                        rps=tx_rate,
                        strategy=strategy,
                        targets=self.quorum.get_targets(),
                        worker=self.worker,
                    )
                    print(f"Starting benchmark {name}")
                    benchmark.start()
                    print(f"Finished benchmark {name}")
        # asyncio.run(self.quorum.stop())

    @staticmethod
    def get_worker_type(jsondata: dict):
        name = str(jsondata["worker"]).capitalize()
        module = importlib.import_module("provisioner.benchmark.workers." + name)
        worker_type = getattr(module, name)
        return worker_type
