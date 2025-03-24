import logging
from random import choice
from typing import override

from web3 import AsyncWeb3, WebSocketProvider
from provinew.quorum.Node import Node
from provinew.quorum.consensus.Consensus import Consensus
import asyncio


class Raft(Consensus):
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

    async def add_learner(self, member: Node):
        validator = choice(self.get_validators())
        assert validator.init_data is not None
        assert member.init_data is not None
        logging.info(f"Connecting to {self.name} to add {member.name} as a learner")
        async with AsyncWeb3(WebSocketProvider(validator.init_data.connection_data.get_ws_url())) as w3:
            await w3.provider.connect()
            joinexisting = await w3.manager.coro_request(
                "raft_addLearner",  # type: ignore
                [member.init_data.get_enode_url()],
            )

        await member.start(joinexisting=joinexisting)

    @override
    def get_consensus_options(self, node: Node, **kwargs):
        assert node.init_data is not None
        options = f"--raft --raftport {node.init_data.connection_data.raft_port} --raftblocktime 1000 "
        if node.role == "member":
            options += f"--raftjoinexisting {kwargs['joinexisting']} "
        return options
