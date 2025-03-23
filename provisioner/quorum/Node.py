import json
from pathlib import Path
import shutil
from typing import Optional

from provisioner.quorum.InitializedNodeData import InitializedNodeData
from provisioner.virtualization.Host import Host
from provisioner.virtualization.Podman import Podman
from provisioner.virtualization.Unikraft import Unikraft
from provisioner.virtualization.VirtManager import VirtManager
from provisioner.virtualization.Virtualizer import Virtualizer
import asyncio


class Node:
    nodes = 0
    role_ids = {"validator": 0, "member": 0}

    def __init__(self, jsondata: dict, consensus: str):
        self.id: int = Node.nodes
        Node.nodes += 1
        self.consensus = consensus
        self.name: str = jsondata["name"]
        self.verbosity = jsondata.get("verbosity", 0)
        self.role: str = jsondata["role"]

        self.role_id: int = Node.role_ids[self.role]
        Node.role_ids[self.role] += 1

        self.virtualizer: Virtualizer = self.get_virtualizer(jsondata["virtualizer"])

        self.init_data: Optional[InitializedNodeData] = None

    async def start(self, **kwargs):
        await self.virtualizer.start(self, **kwargs)

    def get_options(self, **kwargs):
        assert self.init_data is not None
        mapped_dir = self.virtualizer.get_mapped_dir(self)
        options = f"--datadir {mapped_dir.joinpath('data').as_posix()} "
        options += f"--networkid 1234 --nodiscover --verbosity {self.verbosity} "
        options += f"--syncmode full --nousb {self.get_consensus_options(**kwargs)} "
        options += (
            f"--ws --ws.addr 0.0.0.0 --ws.port {self.init_data.ws_port} --ws.origins * "
        )
        options += "--ws.api admin,eth,debug,miner,net,txpool,personal,web3,"
        options += self.consensus + " "
        options += f"--unlock {self.init_data.address} --allow-insecure-unlock --password {mapped_dir.joinpath('data/keystore/accountPassword').as_posix()} "
        options += f"--port {self.init_data.port} "
        return options

    def get_consensus_options(self, **kwargs):
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_role_num(self):
        return self.role + str(self.role_id)

    async def initialize_geth(self, static_nodes: list[str]):
        assert self.init_data is not None
        self.init_data.dir.joinpath("data/permissioned-nodes.json").write_text(
            json.dumps(static_nodes)
        )
        self.init_data.dir.joinpath("data/static-nodes.json").write_text(
            json.dumps(static_nodes)
        )

        process = await asyncio.create_subprocess_exec(
            *f"geth --datadir {self.init_data.dir.joinpath('data')} init {self.init_data.dir.joinpath('data/genesis.json')}".split()
        )
        await process.wait()

    def initialize(
        self,
        node_dir: Path,
        artifacts_path: Path,
    ):
        data = node_dir.joinpath("data")
        keystore = data.joinpath("keystore")
        keystore.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            artifacts_path.joinpath("goQuorum/genesis.json"),
            data.joinpath("genesis.json"),
        )
        role_dir = artifacts_path.joinpath(self.get_role_num())
        for f in ["address", "nodekey", "nodekey.pub"]:
            shutil.copy(role_dir.joinpath(f), data.joinpath(f))
        for f in [
            "accountAddress",
            "accountKeystore",
            "accountPassword",
            "accountPrivateKey",
        ]:
            shutil.copy(role_dir.joinpath(f), keystore.joinpath(f))

        init_data = self.virtualizer.get_init_data(self)
        self.init_data = InitializedNodeData(
            address=keystore.joinpath("accountAddress").read_text().removeprefix("0x"),
            port=init_data["port"],
            ip=init_data["ip"],
            ws_port=init_data["ws_port"],
            raft_port=init_data["raft_port"],
            dir=node_dir,
            enode_hash=node_dir.joinpath("data/nodekey.pub").read_text().strip(),
        )

        self.init_data.dir.joinpath("wsurl").write_text(self.init_data.get_ws_url())

    def get_enode_url(self):
        assert self.init_data is not None
        return self.init_data.get_enode_url()

    @staticmethod
    def get_virtualizer(jsondata: dict):
        match jsondata["name"]:
            case "podman":
                return Podman(jsondata)
            case "host":
                return Host(jsondata)
            case "unikraft":
                return Unikraft(jsondata)
            case "virtmanager":
                return VirtManager(jsondata)
            case _:
                raise NotImplementedError(
                    f"Virtualizer {jsondata['name']} not implemented"
                )
