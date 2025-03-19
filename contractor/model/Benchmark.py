from multiprocessing import Process, Queue
from pathlib import Path
from time import sleep

from model.workers.WorkerStrategy import WorkerStrategy
from model.Logger import Logger
from model.workers.Worker import Worker


class Benchmark:
    def __init__(
        self,
        hosts: list[str],
        rps: int,
        duration: int,
        output_file: Path,
        processes: int,
        timeout: int,
        strategy: WorkerStrategy,
        worker: type[Worker],
    ) -> None:
        self.hosts = hosts
        self.rps = rps
        self.duration = duration
        self.output_file = output_file
        self.processes = processes
        self.timeout = timeout
        self.log_queue = Queue()
        self.strategy = strategy
        self.worker = worker

    def start(self):
        log_queue = Queue()
        logger = Process(
            target=Logger(self, log_queue).run,
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
