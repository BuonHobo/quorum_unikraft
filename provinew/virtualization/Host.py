import asyncio
import logging
import os
from pathlib import Path
import subprocess
from typing import override
from provisioner.virtualization.Virtualizer import HostNetVirtualizer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provisioner.quorum.Node import Node


class Host(HostNetVirtualizer):
    @override
    def get_command(self, node: "Node", **kwargs):
        assert node.init_data is not None
        command = "geth " + node.get_options(**kwargs)
        return command

    @override
    def get_mapped_dir(self, node: "Node") -> Path:
        assert node.init_data is not None
        return node.init_data.dir

    @override
    @staticmethod
    async def stop():
        logging.info("Stopping all geth instances on the host")
        p = await asyncio.create_subprocess_exec(
            "killall",
            "geth",
            start_new_session=True,
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
        env = os.environ.copy()
        env["PRIVATE_CONFIG"] = "ignore"
        subprocess.Popen(
            command,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
