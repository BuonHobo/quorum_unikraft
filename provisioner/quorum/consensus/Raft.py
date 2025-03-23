from random import choice
from typing import override

from web3 import AsyncWeb3, WebSocketProvider
from provisioner.quorum.Node import Node
from provisioner.quorum.consensus.Consensus import Consensus
import asyncio


class Raft(Consensus):
    @staticmethod
    def get_node(nodedata: dict, consensus: str):
        return RaftNode(nodedata, consensus)

    @override
    def get_static_nodes(self):
        return self.get_validators()

    @override
    async def start(self):
        await asyncio.gather(
            *[validator.start() for validator in self.get_validators()]
        )
        await asyncio.gather(
            *[self.add_learner(member) for member in self.get_members()]
        )
        return None

    async def add_learner(self, member: Node):
        validator = choice(self.get_validators())
        assert isinstance(validator, RaftNode)
        joinexisting = await validator.add_learner(member)
        await member.start(joinexisting=joinexisting)


class RaftNode(Node):
    @override
    def get_consensus_options(self, **kwargs):
        assert self.init_data is not None
        options = f"--raft --raftport {self.init_data.raft_port} --raftblocktime 1000 "
        if self.role == "member":
            options += f"--raftjoinexisting {kwargs['joinexisting']} "
        return options

    async def add_learner(self, node: Node):
        assert self.init_data is not None
        assert node.init_data is not None
        async with AsyncWeb3(WebSocketProvider(self.init_data.get_ws_url())) as w3:
            await w3.provider.connect()
            return await w3.manager.coro_request(
                "raft_addLearner",  # type: ignore
                [node.init_data.get_enode_url()],
            )
