from random import choice
from typing import override

from hexbytes import HexBytes
from web3 import AsyncWeb3
from provinew.benchmark.strategies.WorkerStrategy import WorkerStrategy
from eth_account.signers.local import LocalAccount


class Baselinelocal(WorkerStrategy):
    @override
    def __init__(self, *args, **kwargs) -> None:
        self.account: LocalAccount = None  # type: ignore
        raise NotImplementedError("Baselinelocal is not supported anymore")


    @staticmethod
    async def fund_address(connector, address, amount):
        tx_hash = await connector.eth.send_transaction(
            {
                "from": connector.eth.default_account,
                "to": address,
                "value": amount,
                "gas": 25_000_000,
                "gasPrice": 0,
                "chainId": 1337,
            }  # type: ignore
        )
        await connector.eth.wait_for_transaction_receipt(tx_hash)

    @override
    async def prepare_worker(self, worker):
        connector = choice(worker.connectors)
        self.setup_account(connector)
        await self.fund_address(
            connector,
            self.account.address,
            worker.benchmark.duration * worker.benchmark.rps * 2,
        )

    def setup_account(self, connector: AsyncWeb3):
        self.account = connector.eth.account.create()

    @override
    async def send_transaction(self, connector: AsyncWeb3, nonce, pid) -> HexBytes:
        tx = {
            "from": self.account.address,
            "to": connector.eth.default_account,
            "value": 1,
            "nonce": nonce,
            "gas": 25_000_000,
            "gasPrice": 0,
            "chainId": 1337,
        }  # type: ignore
        signed_tx = connector.eth.account.sign_transaction(tx, self.account.key)
        return await connector.eth.send_raw_transaction(signed_tx.raw_transaction)
