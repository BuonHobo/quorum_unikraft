from pathlib import Path
from typing import override

from provinew.quorum.node.NodeData import ConnData
from provinew.utils.Utils import Runner
from provinew.virtualization.Virtualizer import VirtData, Virtualizer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provinew.quorum.node.Node import Node


class Virtmanager(Virtualizer):
    class VirtmanagerData(VirtData):
        @override
        def __init__(self, virtualizer: "Virtualizer", node_ip: str) -> None:
            super().__init__(virtualizer)
            self.node_ip = node_ip

    @override
    def initialize(self, jsondata: dict):
        self.host_ip = jsondata["host_ip"]
        raise NotImplementedError("Virtmanager virtualization is not supported anymore")

    @override
    def handle_node(self, node: "Node", jsondata: dict) -> VirtData:
        return Virtmanager.VirtmanagerData(
            self,
            jsondata["ip"],
        )

    @override
    def get_stop_command(self):
        command = ""
        for node in self.nodes:
            assert isinstance(node.virt_data, Virtmanager.VirtmanagerData)
            ip = node.virt_data.node_ip
            command += f"ssh {ip} killall geth;"
        return command

    @override
    async def pre_start(self, node: "Node"):
        assert isinstance(node.virt_data, Virtmanager.VirtmanagerData)
        command = (
            f"ssh {node.virt_data.node_ip} rm -rf node;"
            f"scp -r {node.get_dir()} {node.virt_data.node_ip}:~/node"
        )
        await Runner.run(command)

    @override
    def get_start_command(self, node: "Node", options: str):
        assert isinstance(node.virt_data, Virtmanager.VirtmanagerData)
        command = f"nohup ssh {node.virt_data.node_ip} geth {options} &> {node.get_dir().joinpath('output.txt')} &"
        return command

    @override
    def get_conn_data(self, node: "Node") -> "ConnData":
        assert isinstance(node.virt_data, Virtmanager.VirtmanagerData)
        return ConnData(
            node.virt_data.node_ip,
            port=30300 + node.id + 1,
            ws_port=32000 + node.id + 1,
            raft_port=53000 + node.id + 1,
        )

    @override
    def get_mapped_dir(self, node: "Node") -> Path:
        return Path("~/node")
