from multiprocessing import Queue
from pathlib import Path
import signal
from time import time


class Logger:
    def __init__(
        self,
        benchmark: "Path",
        log_queue: Queue,
    ) -> None:
        self.output_file = benchmark
        self.log_queue = log_queue

    def run(self):
        start_time = time()
        signal.signal(signal.SIGTERM, handler=lambda x, y: exit(0))
        id = 0
        with self.output_file.open("w") as f:
            f.write("id,pid,host,nonce,sent_time,time_to_send,time_to_rcpt,recv_time\n")
            while True:
                pid, host, nonce, start, send, rcpt = self.log_queue.get()
                f.write(
                    f"{id},{pid},{host},{nonce},{start - start_time:.3f},{send - start:.3f},{rcpt - send:.3f},{rcpt - start_time:.3f}\n"
                )
                f.flush()
                id += 1
