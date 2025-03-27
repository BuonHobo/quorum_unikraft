from provisioner.benchmark.BenchmarkScheduler import BenchmarkScheduler
from provisioner.quorum.Quorum import Quorum


class Experiment:
    def __init__(self, jsondata: dict) -> None:
        self.quorum = Quorum(jsondata["quorum"])
        self.scheduler: BenchmarkScheduler = BenchmarkScheduler(
            self.quorum, jsondata["benchmark"]
        )

    def run(self) -> None:
        self.scheduler.start()
