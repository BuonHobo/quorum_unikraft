import asyncio
from multiprocessing import Array, Lock
from typing import override

from hexbytes import HexBytes
from web3 import AsyncWeb3, WebSocketProvider
from model.workers.Worker import Worker
from model.strategies.WorkerStrategy import WorkerStrategy
from web3.contract import AsyncContract


class NodeContractStrategy(WorkerStrategy):
    @override
    def __init__(
        self,
        contract_address: str,
        contract_abi: str,
        hosts: list[str],
        size: int = 1,
        *args,
        **kwargs,
    ) -> None:
        self.contract_address = contract_address
        self.contract_abi = contract_abi
        self.size = size
        self.contract: AsyncContract = None  # type: ignore
        self.connector_to_contract: dict[AsyncWeb3, AsyncContract] = None  # type: ignore
        self.host_to_id = {host: i for i, host in enumerate(hosts)}
        self.lock: Lock = Lock()  # type: ignore
        self.nonces: Array = Array(  # type: ignore
            "i", asyncio.run(self.init_nonces(hosts)), lock=False
        )

    async def init_nonces(self, hosts: list[str]):
        nonces = []
        for host in hosts:
            async with AsyncWeb3(WebSocketProvider(host)) as connector:
                nonces.append(
                    await connector.eth.get_transaction_count(
                        (await connector.eth.accounts)[0]
                    )
                )
        return nonces

    @override
    async def prepare_worker(self, worker: Worker):
        self.connector_to_contract = {
            connector: connector.eth.contract(
                address=self.contract_address,  # type: ignore
                abi=self.contract_abi,  # type: ignore
            )
            for connector in worker.connectors
        }

    @override
    async def send_transaction(self, connector, nonce, pid) -> HexBytes:
        with self.lock:
            id = self.host_to_id[connector.provider.endpoint_uri]  # type: ignore
            nonce = self.nonces[id]
            self.nonces[id] += 1

        return (
            await self.connector_to_contract[connector]
            .functions.proposeNewValues(
                [f"P{i}" for i in range(self.size)], [i+nonce+pid for i in range(self.size)]
            )
            .transact(
                {
                    "nonce": nonce,
                    "from": connector.eth.default_account,
                    "gas": 25_000_000,
                    "gasPrice": 0,
                    "chainId": 1337,
                }  # type: ignore
            )
        )
