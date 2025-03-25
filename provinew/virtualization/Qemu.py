from pathlib import Path
from typing import override

from provinew.quorum.node.NodeData import ConnData
from provinew.utils.Utils import Runner
from provinew.virtualization.Virtualizer import (
    VirtData,
    Virtualizer,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provinew.quorum.node.Node import Node


class Qemu(Virtualizer):
    class QemuData(VirtData):
        @override
        def __init__(
            self,
            virtualizer: "Virtualizer",
            qcow: Path,
            ssh_port: int,
            memory: str,
            cpus: int,
            user: str,
            key: Path,
        ) -> None:
            super().__init__(virtualizer)
            self.qcow = qcow
            self.ssh_port = ssh_port
            self.memory = memory
            self.cpus = cpus
            self.user = user
            self.key = key

    @override
    def initialize(self, jsondata: dict):
        self.qcow = Path(jsondata["qcow2"])
        self.memory = jsondata["memory"]
        self.cpus = jsondata["cpus"]
        self.user = jsondata["user"]
        self.key = Path(jsondata["key"])

    @override
    def handle_node(self, node: "Node", jsondata: dict) -> VirtData:
        return Qemu.QemuData(
            self,
            Path(jsondata.get("qcow2", self.qcow)),
            node.id + 2000,
            jsondata.get("memory", self.memory),
            jsondata.get("cpus", self.cpus),
            jsondata.get("user", self.user),
            Path(jsondata.get("key", self.key)),
        )

    @override
    def get_stop_command(self):
        command = 'pgrep -f "qemu-system.*-name quorum_" | xargs -r kill -SIGTERM'
        return command

    @override
    async def pre_start(self, node: "Node") -> None:
        assert isinstance(node.virt_data, Qemu.QemuData)
        command = (
            f"qemu-system-x86_64 -drive file={node.virt_data.qcow},format=qcow2,snapshot=on -m {node.virt_data.memory} "
            f"-smp {node.virt_data.cpus} -netdev user,id=net0,hostfwd=tcp::{node.virt_data.ssh_port}-:22"
            f",hostfwd=tcp::{node.get_conn_data().port}-:{node.get_conn_data().port},hostfwd=udp::{node.get_conn_data().port}-:{node.get_conn_data().port}"
            f",hostfwd=tcp::{node.get_conn_data().raft_port}-:{node.get_conn_data().raft_port},hostfwd=udp::{node.get_conn_data().raft_port}-:{node.get_conn_data().raft_port}"
            f",hostfwd=tcp::{node.get_conn_data().ws_port}-:{node.get_conn_data().ws_port},hostfwd=udp::{node.get_conn_data().ws_port}-:{node.get_conn_data().ws_port} "
            f"-device e1000,netdev=net0 -display none "
            f"-name quorum_{node.name} -enable-kvm -daemonize ;"
            f"ssh -i {node.virt_data.key} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {node.virt_data.ssh_port} {node.virt_data.user}@localhost rm -rf node ;"
            f"scp -i {node.virt_data.key} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r -P {node.virt_data.ssh_port} {node.get_dir()} {node.virt_data.user}@localhost:~/node"
        )
        await Runner.run(command)

    @override
    def get_start_command(self, node: "Node", options: str):
        assert isinstance(node.virt_data, Qemu.QemuData)
        command = f"nohup ssh -i {node.virt_data.key} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {node.virt_data.ssh_port} {node.virt_data.user}@localhost geth {options} &> {node.get_dir().joinpath('output.txt')} &"
        return command

    @override
    def get_conn_data(self, node: "Node") -> "ConnData":
        assert isinstance(node.virt_data, Qemu.QemuData)
        return ConnData(
            self.host_ip,
            port=30300 + node.id + 1,
            ws_port=32000 + node.id + 1,
            raft_port=53000 + node.id + 1,
        )

    @override
    def get_mapped_dir(self, node: "Node") -> Path:
        return Path("~/node")
