import asyncio
import importlib
import subprocess
from typing import Optional
from provinew.quorum.Node import Node
from pathlib import Path
import shutil
import logging

from provinew.virtualization.Virtualizer import Virtualizer


class Consensus:
    def __init__(self, jsondata: dict):
        self.name: str = jsondata["name"]
        self.directory: Path = Path(jsondata["directory"]).resolve()
        self.toolbox_container: Optional[str] = jsondata.get("toolboxContainer")

        self.virtualizers = Virtualizer.init_virtualizers(jsondata["virtualizers"])
        self.nodes: list[Node] = [
            Node(node, self, self.virtualizers) for node in jsondata["nodes"]
        ]

    @staticmethod
    def get_consensus(jsondata: dict):
        name = str(jsondata["name"]).capitalize()
        module = importlib.import_module("provinew.quorum.consensus." + name)
        consensus = getattr(module, name)
        return consensus(jsondata)

    def get_consensus_options(self, node: Node, **kwargs):
        raise NotImplementedError("This method must be implemented by the subclass")

    async def start(self):
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_static_nodes(self) -> list[Node]:
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_num_validators(self):
        return sum(node.role == "validator" for node in self.nodes)

    def get_num_members(self):
        return sum(node.role == "member" for node in self.nodes)

    def get_validators(self):
        return [node for node in self.nodes if node.role == "validator"]

    def get_members(self):
        return [node for node in self.nodes if node.role == "member"]

    async def deploy(self):
        await self.stop()
        await self.initialize()
        await self.start()
        logging.info(f"{self.name} consensus deployed")

    async def stop(self):
        await asyncio.gather(*[virtualizer.stop() for virtualizer in self.virtualizers])

    async def initialize(self):
        shutil.rmtree(self.directory, ignore_errors=True)
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

        await asyncio.gather(
            *[
                node.initialize_geth(
                    [n.get_enode_url() for n in self.get_static_nodes()]
                )
                for node in self.nodes
            ]
        )

    async def genesis(self, output_path):
        command = (
            f"toolbox run --container {self.toolbox_container} "
            if self.toolbox_container
            else ""
        )
        command += f"npx quorum-genesis-tool --consensus {self.name} "
        command += "--chainID 1337 --blockperiod 5 --requestTimeout 10 "
        command += "--epochLength 30000 --difficulty 1 --gasLimit 0xFFFFFF "
        command += "--coinbase 0x0000000000000000000000000000000000000000 "
        command += f"--validators {self.get_num_validators()} --members {self.get_num_members()} "
        command += f"--bootnodes 0 --outputPath {output_path}"

        logging.info(f"Generating genesis file for {self.name} consensus")
        process = await asyncio.create_subprocess_exec(
            *command.split(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        await process.wait()
