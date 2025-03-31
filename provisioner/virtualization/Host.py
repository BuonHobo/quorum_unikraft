from pathlib import Path
from typing import override
from provisioner.quorum.node.NodeData import ConnData
from provisioner.virtualization.Virtualizer import Virtualizer, VirtData
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provisioner.quorum.node.Node import Node


class Host(Virtualizer):
    @override
    def initialize(self, jsondata: dict):
        pass

    @override
    def handle_node(self, node: "Node", jsondata: dict) -> VirtData:
        return VirtData(self)

    @override
    def get_stop_command(self):
        return "killall geth"

    @override
    async def pre_start(self, node: "Node"):
        pass

    @override
    def get_start_command(self, node: "Node", options: str):
        command = f"nohup geth {options} &> {node.get_dir().joinpath('output.txt')} &"
        return command

    @override
    def get_env(self, node: "Node") -> dict:
        return {"PRIVATE_CONFIG": "ignore"}

    @override
    def get_conn_data(self, node: "Node") -> "ConnData":
        return ConnData(
            self.host_ip,
            port=30300 + node.id + 1,
            ws_port=32000 + node.id + 1,
            raft_port=53000 + node.id + 1,
        )


    @override
    def get_mapped_dir(self, node: "Node") -> Path:
        return node.get_dir()
    
    @override
    def get_stop_node_command(self, node: "Node") -> str:
        command = (
            f'pgrep -f "{node.get_dir()}" | xargs -r kill -SIGTERM'
        )
        return command