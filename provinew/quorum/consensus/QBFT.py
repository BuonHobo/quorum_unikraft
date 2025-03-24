from typing import override
from provinew.quorum.node.Node import Node
from provinew.quorum.consensus.Consensus import Consensus
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provinew.quorum.Quorum import Quorum


class QBFT(Consensus):
    @override
    def get_static_nodes(self, quorum: "Quorum"):
        return quorum.nodes

    @override
    async def start(self, quorum: "Quorum"):
        await asyncio.gather(
            *[node.start(self.get_consensus_options(node)) for node in quorum.nodes]
        )

    def get_consensus_options(self, node: Node):
        assert node.data is not None
        options = ""
        if node.role == "validator":
            options += "--istanbul.blockperiod 1 "
            options += "--mine "
            options += "--miner.threads 1 "
            options += "--miner.gasprice 0 "
            options += "--emitcheckpoints "
        return options
