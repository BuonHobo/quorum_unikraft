from pathlib import Path
from typing import override

from provisioner.quorum.node.NodeData import ConnData
from provisioner.utils.Utils import Runner
from provisioner.virtualization.Virtualizer import VirtData, Virtualizer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provisioner.quorum.node.Node import Node


class Unikraft(Virtualizer):
    class UnikraftData(VirtData):
        @override
        def __init__(
            self, virtualizer: "Virtualizer", node_ip: str, image: str, memory: str
        ) -> None:
            super().__init__(virtualizer)
            self.image = image
            self.node_ip = node_ip
            self.memory = memory

    @override
    def initialize(self, jsondata: dict):
        self.image = jsondata["image"]
        self.network_name = jsondata["network"]
        self.host_cidr = jsondata["host_cidr"]
        self.memory = jsondata["memory"]
        self.host_ip = self.host_cidr.split("/")[0]
        self.net_started = False

        raise NotImplementedError("Unikraft virtualization is not supported anymore")

    @override
    def handle_node(self, node: "Node", jsondata: dict) -> VirtData:
        return Unikraft.UnikraftData(
            self,
            jsondata["ip"],
            jsondata.get("image", self.image),
            jsondata.get("memory", self.memory),
        )

    @override
    def get_stop_command(self):
        return (
            "sudo KRAFTKIT_NO_WARN_SUDO=1 kraft rm --all ;"
            f"sudo KRAFTKIT_NO_WARN_SUDO=1 kraft net remove {self.network_name}"
        )

    @override
    async def pre_start(self, node: "Node"):
        if not self.net_started:
            await Runner.run(
                "sudo KRAFTKIT_NO_WARN_SUDO=1 kraft net create "
                f"{self.network_name} --network {self.host_cidr}"
            )
            self.net_started = True

    @override
    def get_start_command(self, node: "Node", options: str):
        assert isinstance(node.virt_data, Unikraft.UnikraftData)
        command = (
            f"sudo KRAFTKIT_NO_WARN_SUDO=1 "
            f"kraft run -d --rm "
            f"--name {node.name} "
            f"--network {self.network_name}:{node.virt_data.node_ip} "
            f"-v {node.get_dir()}:/node "
            f"-M {node.virt_data.memory} "
            f"{node.virt_data.image} -- /geth "
            f"{options}"
        )
        return command

    @override
    def get_conn_data(self, node: "Node") -> "ConnData":
        assert isinstance(node.virt_data, Unikraft.UnikraftData)
        return ConnData(
            node.virt_data.node_ip,
            port=30300 + node.id + 1,
            ws_port=32000 + node.id + 1,
            raft_port=53000 + node.id + 1,
        )

    @override
    def get_mapped_dir(self, node: "Node") -> Path:
        return Path("/node")
