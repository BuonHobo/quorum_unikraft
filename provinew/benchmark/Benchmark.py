from multiprocessing import Process, Queue
from pathlib import Path
from time import sleep

from provinew.benchmark.strategies.WorkerStrategy import WorkerStrategy
from provinew.benchmark.Logger import Logger
from provinew.benchmark.workers.Worker import Worker
from provinew.quorum.Quorum import Quorum


class Benchmark:
    def __init__(
        self,
        jsondata: dict,
        quorum: Quorum,
        worker: type[Worker] = Worker,
    ) -> None:
        self.rps = jsondata["tx_rate"]
        self.duration = jsondata["duration"]
        self.output_file = Path(jsondata["output_file"])
        self.processes = jsondata["processes"]
        self.timeout = jsondata["timeout"]
        self.log_queue = Queue()
        self.strategy = WorkerStrategy.get_strategy(jsondata, quorum)
        self.worker = worker
        self.quorum = quorum

    def start(self) -> None:
        self.hosts = [
            node.get_conn_data().get_ws_url() for node in self.quorum.get_targets()
        ]
        self.host_to_name = {
            node.get_conn_data().get_ws_url(): node.name
            for node in self.quorum.get_targets()
        }
        self.nodes = self.quorum.get_targets()
        self.strategy.prepare_strategy()
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
