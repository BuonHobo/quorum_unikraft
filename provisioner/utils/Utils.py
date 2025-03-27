import subprocess
from typing import Optional
import asyncio
import os


class Runner:
    @classmethod
    async def run(cls, command: str, env: Optional[dict] = None):
        if command == "":
            return
        if env is not None:
            env = os.environ.update(env)
        print(f"Running command: {command}")
        p = await asyncio.create_subprocess_shell(
            command, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL
        )
        await p.wait()
