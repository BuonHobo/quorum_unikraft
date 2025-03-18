from multiprocessing import Barrier, Process, Queue
from pathlib import Path
from time import sleep

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