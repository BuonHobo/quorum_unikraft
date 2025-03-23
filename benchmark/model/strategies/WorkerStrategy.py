from hexbytes import HexBytes
from web3 import AsyncWeb3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.workers.Worker import Worker


class WorkerStrategy:
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError()

    async def prepare_worker(self, worker: "Worker") -> None:
        raise NotImplementedError()

    async def send_transaction(
        self, connector: AsyncWeb3, nonce: int, pid: int
    ) -> HexBytes:
        raise NotImplementedError()
