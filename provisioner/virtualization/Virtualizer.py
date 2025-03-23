import asyncio
from pathlib import Path
import socket
from typing import override

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provisioner.quorum.Node import Node


class Virtualizer:
    def __init__(self, jsondata: dict):
        self.name = jsondata["name"]

    @staticmethod
    def stop():
        raise NotImplementedError("This method must be implemented by the subclass")

    async def start(self, node: "Node", **options_kwargs):
        self.prepare(node)
        command = self.get_command(node, **options_kwargs).split()
        p = await asyncio.create_subprocess_exec(*command)
        await p.wait()

    def prepare(self, node: "Node"):
        pass

    def get_command(self, node: "Node", **kwargs) -> str:
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_init_data(self, node: "Node") -> dict:
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_mapped_dir(self, node: "Node") -> Path:
        raise NotImplementedError("This method must be implemented by the subclass")


class HostNetVirtualizer(Virtualizer):
    @override
    def __init__(self, jsondata: dict):
        super().__init__(jsondata)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0)
            s.connect(("1.1.1.1", 1))
            self.host_ip = s.getsockname()[0]

    @override
    def get_init_data(self, node: "Node"):
        data = {
            "ip": self.host_ip,
            "port": 30301 + node.id,
            "ws_port": 32001 + node.id,
            "raft_port": 53001 + node.id,
        }
        return data


class PrivateNetVirtualizer(Virtualizer):
    @override
    def __init__(self, jsondata: dict):
        super().__init__(jsondata)
        self.ip = jsondata["ip"]

    @override
    def get_init_data(self, node: "Node"):
        data = {
            "ip": self.ip,
            "port": 30301 + node.id,
            "ws_port": 32001 + node.id,
            "raft_port": 53001 + node.id,
        }
        return data
