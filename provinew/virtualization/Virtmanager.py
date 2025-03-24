import asyncio
import logging
from pathlib import Path
import subprocess
from typing import override

from provisioner.virtualization.Virtualizer import PrivateNetVirtualizer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provisioner.quorum.Node import Node


class Virtmanager(PrivateNetVirtualizer):
    @override
    def get_command(self, node: "Node", **kwargs):
        assert node.init_data is not None
        command = f"ssh {self.ip} geth " + node.get_options(**kwargs)
        return command

    @override
    def get_mapped_dir(self, node: "Node") -> Path:
        assert node.init_data is not None
        return Path("node")

    @override
    async def prepare(self, node: "Node"):
        assert node.init_data is not None
        logging.info(f"Preparing the {node.name} virtual machine")
        for command in [
            f"ssh {self.ip} killall geth",
            f"ssh {self.ip} rm -rf node",
            f"scp -r {node.init_data.dir} {self.ip}:~/node",
        ]:
            p = await asyncio.create_subprocess_exec(
                *command.split(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            await p.wait()

    @override
    async def start(self, node: "Node", **options_kwargs):
        await self.prepare(node)
        logging.info(f"Starting {node.name}")

        command = self.get_command(node, **options_kwargs).split()
        await asyncio.create_subprocess_exec(
            *command,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
