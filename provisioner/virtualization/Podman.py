import asyncio
from pathlib import Path
from typing import override

from provisioner.virtualization.Virtualizer import HostNetVirtualizer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provisioner.quorum.Node import Node


class Podman(HostNetVirtualizer):
    @override
    def get_command(self, node: "Node", **kwargs):
        assert node.init_data is not None
        command = f"podman run -d --rm --replace --name {node.name} "
        command += (
            f"--label quorum=true --cpus 1 --net host -v {node.init_data.dir}:/node:Z "
        )
        command += "docker.io/quorumengineering/quorum geth "
        command += node.get_options(**kwargs)
        return command

    @override
    def get_mapped_dir(self, node: "Node") -> Path:
        return Path("/node")

    @override
    @staticmethod
    async def stop():
        p = await asyncio.create_subprocess_exec(
            "podman", "rm", "--force", "--filter", "label=quorum=true"
        )
        await p.wait()
