from multiprocessing import Process, Queue
from pathlib import Path
from time import sleep

from provisioner.benchmark.strategies.WorkerStrategy import WorkerStrategy
from provisioner.benchmark.Logger import Logger
from provisioner.benchmark.workers.Simpleworker import Simpleworker
from provisioner.benchmark.workers.Worker import Worker
from provisioner.quorum.node.Node import Node


class Benchmark:
    def __init__(
        self,
        strategy: WorkerStrategy,
        targets: list[Node],
        timeout: int,
        processes: int,
        output_file: Path,
        duration: int,
        rps: int,
        worker: type[Worker] = Simpleworker,
    ) -> None:
        self.rps = rps
        self.duration = duration
        self.output_file = output_file
        self.processes = processes
        self.timeout = timeout
        self.log_queue = Queue()
        self.strategy = strategy
        self.worker = worker
        self.targets = targets
        self.hosts = [target.get_conn_data().get_ws_url() for target in targets]
        self.host_to_name = {
            target.get_conn_data().get_ws_url(): target.name for target in targets
        }

    def start(self) -> None:
        self.strategy.prepare_strategy()
        log_queue = Queue()
        logger = Process(
            target=Logger(self.output_file, log_queue).run,
        )
        logger.start()

        subprocesses = self.worker.get_pool(
            self, log_queue, self.processes, self.strategy
        )
        for process in subprocesses:
            process.start()
        for process in subprocesses:
            process.join()

        sleep(1)
        logger.terminate()
