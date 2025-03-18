from random import choice
from typing import override

from hexbytes import HexBytes
from model.workers.Worker import Worker
from eth_account.signers.local import LocalAccount
from web3.contract import AsyncContract


class ContractWorker(Worker):
    @override
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.account: LocalAccount = None  # type: ignore
        self.contract: AsyncContract = None  # type: ignore

    async def setup_account(self):
        self.account = choice(self.connectors).eth.account.create()
        pass

    @override
    async def prepare(self):
        self.contract = choice(self.connectors).eth.contract(
            address=self.worker_args["contract_address"],  # type: ignore
            abi=self.worker_args["contract_abi"],  # type: ignore
        )

    @override
    async def prepare_transaction(self, connector, nonce, **kwargs) -> HexBytes:
        tx = await self.contract.functions.proposeNewValues(
            ["P0"], [nonce]
        ).build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "gas": 25_000_000,
                "gasPrice": 0,
                "chainId": 1337,
            }  # type: ignore
        )
        return connector.eth.account.sign_transaction(tx, self.account.key)
