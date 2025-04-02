from pathlib import Path
from typing import override

from provisioner.quorum.node.NodeData import ConnData
from provisioner.virtualization.Virtualizer import (
    VirtData,
    Virtualizer,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provisioner.quorum.node.Node import Node


class Unitest(Virtualizer):
    class UnitestData(VirtData):
        @override
        def __init__(self, virtualizer: "Virtualizer", image: str, memory: str) -> None:
            super().__init__(virtualizer)
            self.image = image
            self.memory = memory

    @override
    def initialize(self, jsondata: dict):
        self.image = jsondata["image"]
        self.memory = jsondata["memory"]

    @override
    def handle_node(self, node: "Node", jsondata: dict) -> VirtData:
        return Unitest.UnitestData(
            self,
            jsondata.get("image", self.image),
            jsondata.get("memory", self.memory),
        )

    @override
    def get_stop_command(self):
        return "kraft rm --all"

    @override
    async def pre_start(self, node: "Node"):
        pass

    @override
    def get_start_command(self, node: "Node", options: str):
        assert isinstance(node.virt_data, Unitest.UnitestData)
        command = (
            f"nohup " 
            f"kraft run --rm "
            f"--name {node.name} "
            f"-p {node.get_conn_data().port}:{node.get_conn_data().port} "
            f"-p {node.get_conn_data().raft_port}:{node.get_conn_data().raft_port} "
            f"-p {node.get_conn_data().ws_port}:{node.get_conn_data().ws_port} "
            f"-v {node.get_dir()}:/node "
            f"-M {node.virt_data.memory} "
            f"{node.virt_data.image} -- /geth "
            f"{options} "
            f"&> {node.get_dir().joinpath('output.txt')} &"
        )
        return command

    @override
    def get_conn_data(self, node: "Node") -> "ConnData":
        assert isinstance(node.virt_data, Unitest.UnitestData)
        return ConnData(
            self.host_ip,
            port=30300 + node.id + 1,
            ws_port=32000 + node.id + 1,
            raft_port=53000 + node.id + 1,
        )

    @override
    def get_mapped_dir(self, node: "Node") -> Path:
        return Path("/node")

    @override
    def get_stop_node_command(self, node: "Node") -> str:
        return f"kraft rm {node.name}"
