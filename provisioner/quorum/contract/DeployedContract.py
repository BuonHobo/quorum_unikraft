import asyncio
from web3.contract import AsyncContract


class DeployedContract:
    def __init__(self, address, abi, parameters, agents, numagents4params):
        self.address = address
        self.abi = abi
        self.parameters = parameters
        self.agents = agents
        self.numagents4params = numagents4params

    async def subscribe(self, node, event_name, callback):
        async with await node.connect() as w3:
            contractInstance: AsyncContract = w3.eth.contract(
                address=self.address, abi=self.abi
            )
            filter = await contractInstance.events[event_name].create_filter(
                from_block="latest"
            )

            while True:
                for event in await filter.get_new_entries():
                    await callback(event)
                await asyncio.sleep(1)

    async def transact(self, node, method, args):
        async with await node.connect() as w3:
            contractInstance = w3.eth.contract(address=self.address, abi=self.abi)
            tx_hash = await contractInstance.functions[method](*args).transact()
            tx_receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
            return tx_receipt

    async def call(self, node, method, args):
        async with await node.connect() as w3:
            contractInstance = w3.eth.contract(address=self.address, abi=self.abi)
            return await contractInstance.functions[method](*args).call()
