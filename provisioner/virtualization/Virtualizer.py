import importlib
from pathlib import Path

import socket
from typing import TYPE_CHECKING, Optional

from provisioner.utils.Utils import Runner

if TYPE_CHECKING:
    from provisioner.quorum.node.Node import Node
    from provisioner.quorum.node.NodeData import ConnData


class VirtData:
    def __init__(self, virtualizer: "Virtualizer") -> None:
        self.virtualizer = virtualizer


class Virtualizer:
    def handle_node(self, node: "Node", jsondata: dict) -> VirtData:
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_stop_command(self) -> str:
        raise NotImplementedError("This method must be implemented by the subclass")

    async def pre_start(self, node: "Node"):
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_start_command(self, node: "Node", options: str) -> str:
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_conn_data(self, node: "Node") -> "ConnData":
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_mapped_dir(self, node: "Node") -> Path:
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_env(self, node: "Node") -> Optional[dict]:
        return

    def initialize(self, jsondata: dict):
        raise NotImplementedError("This method must be implemented by the subclass")

    def __init__(self, jsondata: dict):
        self.name = jsondata["name"]
        self.nodes: list["Node"] = []
        self.initialize(jsondata)
        self.host_ip = self.get_default_ip()

    def get_default_ip(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0)
            s.connect(("1.1.1.1", 1))
            return s.getsockname()[0]

    def add_node(self, node: "Node", jsondata: dict) -> VirtData:
        self.nodes.append(node)
        return self.handle_node(node, jsondata)

    async def stop(self):
        cmd = self.get_stop_command()
        await Runner.run(cmd)

    async def start(self, node: "Node", options: str):
        cmd = self.get_start_command(node, options)
        env = self.get_env(node)
        node.get_dir().joinpath("cmd").write_text(cmd)
        await self.pre_start(node)
        await Runner.run(cmd, env)

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
        return jsondata["name"], virtualizer(jsondata)