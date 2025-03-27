import asyncio
from multiprocessing import Array, Lock
from random import choices
from typing import override

from hexbytes import HexBytes
from web3 import AsyncWeb3, WebSocketProvider
from provisioner.benchmark.workers.Worker import Worker
from provisioner.benchmark.strategies.WorkerStrategy import WorkerStrategy
from web3.contract import AsyncContract

from provisioner.quorum.Quorum import Quorum


class Contract(WorkerStrategy):
    @override
    def __init__(
        self,
        jsondata: dict,
        quorum: Quorum,
    ) -> None:
        self.quorum = quorum
        self.size = jsondata["tx_size"]
        self.parameters = quorum.get_contract().get_parameters()
        self.contract: AsyncContract = None  # type: ignore
        self.connector_to_contract: dict[AsyncWeb3, AsyncContract] = None  # type: ignore
        self.lock: Lock = Lock()  # type: ignore

    @override
    def prepare_strategy(self):
        hosts = [
            node.get_conn_data().get_ws_url() for node in self.quorum.get_targets()
        ]
        self.host_to_id = {host: i for i, host in enumerate(hosts)}
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
        self.connector_to_contract = { # type: ignore
            connector: connector.eth.contract(
                address=self.quorum.get_contract().get_address(),  # type: ignore
                abi=self.quorum.get_contract().get_abi(),  # type: ignore
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
                choices(self.parameters, k=self.size),
                [i + nonce + pid for i in range(self.size)],
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

    @override
    def get_name(self) -> str:
        return f"contract-{self.size}"