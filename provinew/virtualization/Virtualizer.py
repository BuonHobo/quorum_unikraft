import asyncio
import importlib
import logging
from pathlib import Path
import subprocess

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from provinew.quorum.Node import Node
    from provinew.quorum.NodeData import ConnData


class Virtualizer:
    def __init__(self, jsondata: dict):
        self.name = jsondata["name"]
        self.nodes = []

    def add_node(self, node: "Node"):
        self.nodes.append(node)
        self.handle_node(node)

    def handle_node(self, node: "Node"):
        raise NotImplementedError("This method must be implemented by the subclass")

    def stop(self):
        raise NotImplementedError("This method must be implemented by the subclass")

    async def start(self, node: "Node", **options_kwargs):
        logging.info(f"Starting {node.name}")
        await self.prepare(node)
        command = self.get_command(node, **options_kwargs).split()
        p = await asyncio.create_subprocess_exec(
            *command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        await p.wait()
        await asyncio.sleep(1)

    async def prepare(self, node: "Node"):
        pass

    def get_command(self, node: "Node", **kwargs) -> str:
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_conn_data(self, node: "Node") -> "ConnData":
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_mapped_dir(self, node: "Node") -> Path:
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_mapped_ip(self, node: "Node") -> str:
        raise NotImplementedError("This method must be implemented by the subclass")

    @staticmethod
    def init_virtualizers(virtualizers: list[dict]):
        result = {}
        for virtualizer in virtualizers:
            name, virtualizer = Virtualizer.get_virtualizer(virtualizer)
            result[name] = virtualizer
        return result

    @staticmethod
    def get_virtualizer(jsondata: dict):
        name = str(jsondata["name"]).capitalize()
        module = importlib.import_module("provinew.virtualization." + name)
        virtualizer = getattr(module, name)
        return name, virtualizer(jsondata)
