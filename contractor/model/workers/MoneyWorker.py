from random import choice
from typing import override

from hexbytes import HexBytes
from model.workers.Worker import Worker
from eth_account.signers.local import LocalAccount


class MoneyWorker(Worker):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.account: LocalAccount = None  # type: ignore

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
    async def prepare(self):
        await self.fund_address(
            choice(self.connectors),
            self.account.address,
            self.benchmark.duration * self.benchmark.rps * 2,
        )

    async def setup_account(self):
        self.account = choice(self.connectors).eth.account.create()
        pass

    @override
    async def prepare_transaction(self, connector, nonce, **kwargs) -> HexBytes:
        tx = {
            "from": self.account.address,
            "to": connector.eth.default_account,
            "value": 1,
            "nonce": nonce,
            "gas": 25_000_000,
            "gasPrice": 0,
            "chainId": 1337,
        }  # type: ignore
        return connector.eth.account.sign_transaction(tx, self.account.key)
