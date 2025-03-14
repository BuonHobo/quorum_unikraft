import asyncio

class Logger:
    def __init__(self):
        self.transactions = []
    
    def schedule_log(self, transaction):
        self.transactions.append(transaction)

    async def log(self):
        while True:
            if len(self.transactions) > 0:
                for transaction in self.transactions:
                    print(transaction)
                self.transactions.clear()
            await asyncio.sleep(1)