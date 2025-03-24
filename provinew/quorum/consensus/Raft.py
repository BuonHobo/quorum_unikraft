from random import choice
from typing import override

from web3 import AsyncWeb3, WebSocketProvider
from provinew.quorum.node.Node import Node
from provinew.quorum.consensus.Consensus import Consensus

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provinew.quorum.Quorum import Quorum


class Raft(Consensus):
    @override
    def get_static_nodes(self, quorum: "Quorum"):
        return quorum.get_validators()

    @override
    async def start(self, quorum: "Quorum"):
        validators = quorum.get_validators()
        for validator in validators:
            await validator.start(self.get_consensus_options(validator))
        validator = choice(validators)
        for member in quorum.get_members():
            await self.add_learner(member, validator)

    async def add_learner(self, member: Node, validator: Node):
        assert validator.data is not None
        assert member.data is not None
        async with AsyncWeb3(
            WebSocketProvider(validator.data.connection_data.get_ws_url())
        ) as w3:
            await w3.provider.connect()
            joinexisting = await w3.manager.coro_request(
                "raft_addLearner",  # type: ignore
                [member.data.get_enode_url()],
            )

        await member.start(
            self.get_consensus_options(member, joinexisting=joinexisting)
        )

    def get_consensus_options(self, node: Node, joinexisting: str = ""):
        assert node.data is not None
        options = (
            "--raft "
            f"--raftport {node.data.connection_data.raft_port} "
            "--raftblocktime 1000"
        )
        if node.role == "member":
            options += f" --raftjoinexisting {joinexisting}"
        return options
