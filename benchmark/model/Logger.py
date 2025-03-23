from multiprocessing import Queue
import signal
from time import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.Benchmark import Benchmark

class Logger:
    def __init__(
        self,
        benchmark: "Benchmark",
        log_queue: Queue,
    ) -> None:
        self.benchmark = benchmark
        self.log_queue = log_queue

    def run(self):
        start_time = time()
        signal.signal(signal.SIGTERM, handler=lambda x, y: exit(0))
        id = 0
        with self.benchmark.output_file.open("w") as f:
            f.write("id,pid,host,nonce,sent_time,time_to_send,time_to_rcpt,recv_time\n")
            while True:
                pid, host, nonce, start, send, rcpt = self.log_queue.get()
                f.write(
                    f"{id},{pid},{host},{nonce},{start - start_time:.3f},{send - start:.3f},{rcpt - send:.3f},{rcpt - start_time:.3f}\n"
                )
                f.flush()
                id += 1
