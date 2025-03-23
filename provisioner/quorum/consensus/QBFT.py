from typing import override
from provisioner.quorum.Node import Node
from provisioner.quorum.consensus.Consensus import Consensus
import asyncio


class QBFT(Consensus):
    @staticmethod
    def get_node(nodedata: dict, consensus: str):
        return QBFTNode(nodedata, "istanbul")

    @override
    def get_static_nodes(self):
        return self.nodes

    @override
    async def start(self):
        await asyncio.gather(*[node.start() for node in self.nodes])


class QBFTNode(Node):
    @override
    def get_consensus_options(self, **kwargs):
        assert self.init_data is not None
        options = ""
        if self.role == "validator":
            options += "--istanbul.blockperiod 1 --mine --miner.threads 1 --miner.gasprice 0 --emitcheckpoints "
        return options
