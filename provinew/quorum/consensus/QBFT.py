from typing import override
from provinew.quorum.Node import Node
from provinew.quorum.consensus.Consensus import Consensus
import asyncio


class QBFT(Consensus):
    @override
    def get_static_nodes(self):
        return self.nodes

    @override
    async def start(self):
        await asyncio.gather(*[node.start() for node in self.nodes])

    @override
    def get_consensus_options(self, node:Node, **kwargs):
        assert node.init_data is not None
        options = ""
        if node.role == "validator":
            options += "--istanbul.blockperiod 1 --mine --miner.threads 1 --miner.gasprice 0 --emitcheckpoints "
        return options
