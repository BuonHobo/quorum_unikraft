from typing import override
from provisioner.quorum.node.Node import Node
from provisioner.quorum.consensus.Consensus import Consensus
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provisioner.quorum.Quorum import Quorum


class Qbft(Consensus):
    @override
    def get_static_nodes(self, quorum: "Quorum"):
        return quorum.nodes

    @override
    async def start(self, quorum: "Quorum"):
        for node in quorum.nodes:
            await node.start(self.get_consensus_options(node))

    def get_consensus_options(self, node: Node):
        options = ""
        if node.role == "validator":
            options += "--istanbul.blockperiod 1 "
            options += "--mine "
            options += "--miner.threads 1 "
            options += "--miner.gasprice 0 "
            options += "--emitcheckpoints "
        return options
