from random import choice
from provinew.quorum.consensus.Consensus import Consensus
import asyncio
from typing import Optional
from provinew.quorum.contract.IDSContract import Contract
from provinew.quorum.node.Node import Node
from pathlib import Path
import shutil

from provinew.utils.Utils import Runner
from provinew.virtualization.Virtualizer import Virtualizer


class Quorum:
    def __init__(self, jsondata: dict):
        self.directory: Path = Path(jsondata["directory"]).resolve()
        self.toolbox_container: Optional[str] = jsondata.get("toolboxContainer")
        self.consensus: Consensus = Consensus.get_consensus(jsondata)
        virtualizers = Virtualizer.init_virtualizers(jsondata["virtualizers"])
        self.virtualizers = virtualizers.values()
        self.nodes: list[Node] = [
            Node(node, virtualizers) for node in jsondata["nodes"]
        ]
        self.contract: Contract = Contract(self.get_agents(), jsondata["contract"])

    def get_agents(self):
        return [node for node in self.nodes if node.agent]

    def get_targets(self):
        return [node for node in self.nodes if node.target]

    def get_num_validators(self):
        return sum(node.role == "validator" for node in self.nodes)

    def get_num_members(self):
        return sum(node.role == "member" for node in self.nodes)

    def get_validators(self):
        return [node for node in self.nodes if node.role == "validator"]

    def get_members(self):
        return [node for node in self.nodes if node.role == "member"]

    async def deploy_contract(self):
        await self.contract.deploy_using_node(choice(self.nodes))

    async def stop(self):
        for virtualizer in self.virtualizers:
            await virtualizer.stop()

    async def start(self):
        await self.consensus.start(self)

    async def initialize(self) -> None:
        await Runner.run(f"rm -rf {self.directory}")
        self.directory.mkdir(parents=True, exist_ok=True)

        output_path = self.directory.joinpath("artifacts_tmp")
        artifacts_path = self.directory.joinpath("artifacts")
        await self.genesis(output_path)

        tmp_path = next(output_path.iterdir())
        tmp_path.rename(artifacts_path)

        shutil.rmtree(output_path, ignore_errors=True)

        for node in self.nodes:
            node.initialize(self.directory.joinpath(node.name), artifacts_path)

        shutil.rmtree(artifacts_path, ignore_errors=True)

        coros = []
        for node in self.nodes:
            coro = node.initialize_geth(self.consensus.get_static_nodes(self))
            coros.append(coro)
        await asyncio.gather(*coros)

    async def genesis(self, output_path):
        command = ""

        if self.toolbox_container:
            command += f"toolbox run --container {self.toolbox_container} "

        command += (
            f"npx quorum-genesis-tool --consensus {self.consensus.name} "
            "--chainID 1337 "
            "--blockperiod 5 "
            "--requestTimeout 10 "
            "--epochLength 30000 "
            "--difficulty 1 "
            "--gasLimit 0xFFFFFF "
            "--coinbase 0x0000000000000000000000000000000000000000 "
            f"--validators {self.get_num_validators()} "
            f"--members {self.get_num_members()} "
            "--bootnodes 0 "
            f"--outputPath {output_path}"
        )

        await Runner.run(command)
