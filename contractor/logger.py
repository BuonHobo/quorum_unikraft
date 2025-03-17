from pathlib import Path
from multiprocessing import Queue


class Logger:
    def __init__(self):
        self.transactions = Queue()

    def schedule_log(self,host, key, id, time_start, time_send, time_rcpt):
        self.transactions.put(
            f"{host:3},{key:3},{id:8},{time_start - self.global_start:8.3f},{time_send - time_start:8.3f},{time_rcpt - time_send:8.3f},{time_rcpt - self.global_start:8.3f}\n"
        )
        if self.transactions.qsize() > 100:
            print("logging")
            self.log()

    def log(self):
        print("Logging")
        while not self.transactions.empty():
            self.f.write(self.transactions.get())

    def start_time(self, time):
        self.global_start = time

    def set_output(self, output):
        self.output: Path = output
        self.output.touch()
        self.f = output.open("w")
