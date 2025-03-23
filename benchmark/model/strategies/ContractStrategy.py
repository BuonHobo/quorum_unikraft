from random import choice
from typing import override

from hexbytes import HexBytes
from web3 import AsyncWeb3
from model.strategies.WorkerStrategy import WorkerStrategy
from eth_account.signers.local import LocalAccount
from web3.contract import AsyncContract


class ContractStrategy(WorkerStrategy):
    @override
    def __init__(
        self, contract_address: str, contract_abi: str, *args, **kwargs
    ) -> None:
        self.contract_address = contract_address
        self.contract_abi = contract_abi
        self.account: LocalAccount = None  # type: ignore
        self.contract: AsyncContract = None  # type: ignore

    def setup_account(self, connector: AsyncWeb3):
        self.account = connector.eth.account.create()

    @override
    async def prepare_worker(self, worker):
        connector = choice(worker.connectors)
        self.setup_account(connector)
        self.contract = connector.eth.contract(
            address=self.contract_address,  # type: ignore
            abi=self.contract_abi,  # type: ignore
        )

    @override
    async def send_transaction(self, connector, nonce, pid) -> HexBytes:
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
        signed_tx = connector.eth.account.sign_transaction(tx, self.account.key)
        return await connector.eth.send_raw_transaction(signed_tx.raw_transaction)
