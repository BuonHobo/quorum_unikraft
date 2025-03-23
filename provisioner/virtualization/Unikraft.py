import asyncio
from pathlib import Path
import subprocess
from typing import override

from provisioner.virtualization.Virtualizer import PrivateNetVirtualizer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provisioner.quorum.Node import Node


class Unikraft(PrivateNetVirtualizer):
    net_started = False

    @override
    def __init__(self, jsondata: dict):
        super().__init__(jsondata)
        self.network = "deployment"
        self.partial_ip = ".".join(self.ip.split(".")[0:3])

    def start_network(self):
        if not Unikraft.net_started:
            command = f"sudo KRAFTKIT_NO_WARN_SUDO=1 kraft net create {self.network} --network {self.partial_ip}.254/24"
            subprocess.Popen(command.split(), stdin=subprocess.DEVNULL).wait()
            Unikraft.net_started = True

    @override
    def prepare(self, node: "Node"):
        self.start_network()

    @override
    def get_command(self, node: "Node", **kwargs):
        assert node.init_data is not None
        command = (
            f"sudo KRAFTKIT_NO_WARN_SUDO=1 kraft run --rm --detach --name {node.name} "
        )
        command += (
            f"--network {self.network}:{self.ip} -v {node.init_data.dir}:/node -M 1Gi "
        )
        command += "buonhobo/geth -- /geth "
        command += node.get_options(**kwargs)
        return command

    @override
    def get_mapped_dir(self, node: "Node") -> Path:
        return Path("/node")

    @override
    @staticmethod
    async def stop():
        p = await asyncio.create_subprocess_exec(
            *"sudo KRAFTKIT_NO_WARN_SUDO=1 kraft rm --all".split()
        )
        await p.wait()
        p2 = await asyncio.create_subprocess_exec(
            *"sudo KRAFTKIT_NO_WARN_SUDO=1 kraft net remove deployment".split()
        )
        await p2.wait()
