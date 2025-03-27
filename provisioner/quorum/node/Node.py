import json
from pathlib import Path
import shutil
from typing import Optional, Self

from web3 import AsyncWeb3, WebSocketProvider
from web3.middleware import ExtraDataToPOAMiddleware


from provisioner.quorum.node.NodeData import NodeData

from typing import TYPE_CHECKING

from provisioner.utils.Utils import Runner

if TYPE_CHECKING:
    from provisioner.virtualization.Virtualizer import Virtualizer, VirtData


class Node:
    nodes = 0
    role_ids = {"validator": 0, "member": 0}

    def __init__(
        self,
        jsondata: dict,
        virtualizers: dict[str, "Virtualizer"],
    ):
        self.name: str = jsondata["name"]
        self.verbosity = jsondata.get("verbosity", 0)
        self.role: str = jsondata["role"]
        self.agent: bool = jsondata.get("agent", False)
        self.target: bool = jsondata.get("target", False)

        self.id: int = Node.nodes
        Node.nodes += 1
        self.role_id: int = Node.role_ids[self.role]
        Node.role_ids[self.role] += 1

        self.virt_data: "VirtData" = virtualizers[
            jsondata["virtualizer"]["name"]
        ].add_node(self, jsondata["virtualizer"])
        self.data: Optional[NodeData] = None

    async def start(self, consensus_options: str) -> None:
        await self.virt_data.virtualizer.start(
            self, self.get_options() + " " + consensus_options
        )

    async def send(self, to_node: Self, value: int) -> None:
        async with await self.connect() as w3:
            tx_hash = await w3.eth.send_transaction(
                {"to": to_node.get_checksum_address(), "value": value}
            )
            _tx_receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)

    async def connect(self):
        assert self.data is not None
        w3: AsyncWeb3 = await AsyncWeb3(
            WebSocketProvider(self.data.connection_data.get_ws_url())
        )
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        w3.eth.default_account = self.get_checksum_address()
        return w3

    def get_conn_data(self):
        assert self.data is not None
        return self.data.connection_data

    def get_dir(self):
        assert self.data is not None
        return self.data.dir

    def get_checksum_address(self):
        assert self.data is not None
        return AsyncWeb3.to_checksum_address("0x" + self.data.address)

    def get_address(self):
        assert self.data is not None
        return self.data.address

    def get_options(self):
        assert self.data is not None
        mapped_dir = self.virt_data.virtualizer.get_mapped_dir(self)
        options = (
            f"--datadir {mapped_dir.joinpath('data').as_posix()} "
            f"--networkid 1234 "
            f"--nodiscover "
            f"--verbosity {self.verbosity} "
            f"--ws "
            f"--ws.addr 0.0.0.0 "
            f"--ws.port {self.data.connection_data.ws_port} "
            f"--ws.origins '*' "
            f"--ws.api admin,eth,debug,miner,net,txpool,personal,web3,raft,istanbul "
            f"--syncmode full "
            f"--nousb "
            f"--unlock {self.data.address} "
            f"--allow-insecure-unlock "
            f"--password {mapped_dir.joinpath('data/keystore/accountPassword').as_posix()} "
            f"--port {self.data.connection_data.port} "
        )
        return options

    def get_role_num(self):
        return self.role + str(self.role_id)

    async def initialize_geth(self, static_nodes: list[Self]):
        enodes = []
        for node in static_nodes:
            enodes.append(node.get_enode_url())

        assert self.data is not None
        self.data.dir.joinpath("data/permissioned-nodes.json").write_text(
            json.dumps(enodes)
        )
        self.data.dir.joinpath("data/static-nodes.json").write_text(json.dumps(enodes))
        await Runner.run(
            f"geth --datadir {self.data.dir.joinpath('data')} init {self.data.dir.joinpath('data/genesis.json')}"
        )

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

        conn_data = self.virt_data.virtualizer.get_conn_data(self)
        self.data = NodeData(
            address=keystore.joinpath("accountAddress").read_text().removeprefix("0x"),
            connection_data=conn_data,
            dir=node_dir,
            enode_hash=node_dir.joinpath("data/nodekey.pub").read_text().strip(),
        )

        self.data.dir.joinpath("wsurl").write_text(
            self.data.connection_data.get_ws_url()
        )
        self.data.dir.joinpath("enode").write_text(self.data.get_enode_url())

    def get_enode_url(self):
        assert self.data is not None
        return self.data.get_enode_url()
