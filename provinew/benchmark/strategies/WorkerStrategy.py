from __future__ import annotations

import importlib
from hexbytes import HexBytes
from web3 import AsyncWeb3
from typing import TYPE_CHECKING

from provinew.quorum.Quorum import Quorum

if TYPE_CHECKING:
    from provinew.benchmark.workers.Worker import Worker


class WorkerStrategy:
    def __init__(self, jsondata: dict, quorum: Quorum) -> None:
        raise NotImplementedError()

    def prepare_strategy(self) -> None:
        raise NotImplementedError()

    async def prepare_worker(self, worker: "Worker") -> None:
        raise NotImplementedError()

    async def send_transaction(
        self, connector: AsyncWeb3, nonce: int, pid: int
    ) -> HexBytes:
        raise NotImplementedError()

    @staticmethod
    def get_strategy(jsondata: dict, quorum: Quorum) -> WorkerStrategy:
        name = str(jsondata["strategy"]).capitalize()
        module = importlib.import_module("provinew.benchmark.strategies." + name)
        strategy = getattr(module, name)
        return strategy(jsondata, quorum)
