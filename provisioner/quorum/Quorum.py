from random import choice
from provisioner.quorum.consensus.Consensus import Consensus
import asyncio
from typing import Optional
from provisioner.quorum.contract.IDSContract import Contract
from provisioner.quorum.node.Node import Node
from pathlib import Path
import shutil

from provisioner.utils.Utils import Runner
from provisioner.virtualization.Virtualizer import Virtualizer


class Quorum:
    def __init__(self, jsondata: dict):
        self.__directory: Path = Path(jsondata["directory"]).resolve()
        self.__toolbox_container: Optional[str] = jsondata.get("toolboxContainer")
        self.__consensus: Consensus = Consensus.get_consensus(jsondata)
        virtualizers = Virtualizer.init_virtualizers(jsondata["virtualizers"])
        self.__virtualizers = virtualizers.values()
        self.__nodes: list[Node] = [
            Node(node, virtualizers) for node in jsondata["nodes"]
        ]
        self.__contract: Contract = Contract(self.get_agents(), jsondata["contract"])
        self.__initialized = False

    def get_consensus(self):
        return self.__consensus.name

    def get_contract(self):
        assert self.__contract is not None
        return self.__contract

    def get_agents(self):
        return [node for node in self.__nodes if node.agent]

    def get_targets(self):
        return [node for node in self.__nodes if node.target]

    def get_num_validators(self):
        return sum(node.role == "validator" for node in self.__nodes)

    def get_num_members(self):
        return sum(node.role == "member" for node in self.__nodes)

    def get_validators(self):
        return [node for node in self.__nodes if node.role == "validator"]

    def get_members(self):
        return [node for node in self.__nodes if node.role == "member"]

    async def deploy_contract(self):
        await self.__contract.deploy_using_node(choice(self.__nodes))

    async def stop(self):
        for virtualizer in self.__virtualizers:
            await virtualizer.stop()

    async def stop_nodes(self):
        for node in self.__nodes:
            await node.stop()

    async def start(self):
        await self.__consensus.start(self)
        await asyncio.sleep(3)
        return await self.deploy_contract()

    async def make_artifacts(self):
        output_path = self.__directory.joinpath("artifacts_tmp")
        await self.genesis(output_path)

        tmp_path = next(output_path.iterdir())

        artifacts_path = self.__directory.joinpath("artifacts")
        tmp_path.rename(artifacts_path)

        shutil.rmtree(output_path, ignore_errors=True)

        return artifacts_path

    async def remove_deployment(self):
        await Runner.run(f"rm -rf {self.__directory}")

    async def remove_nodes(self):
        for node in self.__nodes:
            shutil.rmtree(node.get_dir(), ignore_errors=True)

    async def initialize_nodes(self, artifacts_path):
        for node in self.__nodes:
            node.initialize(self.__directory.joinpath(node.name), artifacts_path)

        coros = []
        for node in self.__nodes:
            coro = node.initialize_geth(self.__consensus.get_static_nodes(self))
            coros.append(coro)
        await asyncio.gather(*coros)

    async def initialize(self) -> None:
        await self.remove_deployment()

        self.__directory.mkdir(parents=True, exist_ok=True)

        artifacts_path = await self.make_artifacts()

        await self.initialize_nodes(artifacts_path)

        self.__initialized = True

    async def restart(self):
        if not self.__initialized:
            await self.stop()
            await self.initialize()
        else:
            self.__contract.discard_instance()
            await self.stop_nodes()
            await self.remove_nodes()
            await self.initialize_nodes(self.__directory.joinpath("artifacts"))
        await self.start()
        await asyncio.sleep(5)

    async def genesis(self, output_path):
        command = ""

        if self.__toolbox_container:
            command += f"toolbox run --container {self.__toolbox_container} "

        command += (
            f"npx quorum-genesis-tool --consensus {self.__consensus.name} "
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
