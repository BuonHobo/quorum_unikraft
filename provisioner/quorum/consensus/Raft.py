from random import choice
from typing import override

from provisioner.quorum.node.Node import Node
from provisioner.quorum.consensus.Consensus import Consensus

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provisioner.quorum.Quorum import Quorum


class Raft(Consensus):
    @override
    def get_static_nodes(self, nodes: list[Node]):
        return [node for node in nodes if node.role == "validator"]

    @override
    async def start(self, quorum: "Quorum"):
        validators = quorum.get_validators()
        for validator in validators:
            await validator.start(self.get_consensus_options(validator))
        validator = choice(validators)
        for member in quorum.get_members():
            await self.add_learner(member, validator)

    async def add_learner(self, member: Node, validator: Node):
        async with await validator.connect() as w3:
            joinexisting = await w3.manager.coro_request(
                "raft_addLearner",  # type: ignore
                [member.get_enode_url()],
            )

        await member.start(
            self.get_consensus_options(member, joinexisting=joinexisting)
        )

    def get_consensus_options(self, node: Node, joinexisting: str = ""):
        options = (
            f"--raft --raftport {node.get_conn_data().raft_port} --raftblocktime 1000"
        )
        if node.role == "member":
            options += f" --raftjoinexisting {joinexisting}"
        return options
