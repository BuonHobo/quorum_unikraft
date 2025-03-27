from pathlib import Path
import solcx
from web3 import AsyncWeb3

from provisioner.quorum.node.Node import Node


class ContractBuilder:
    def __init__(self, jsondata: dict, agents: list[Node]):
        self.path = Path(jsondata["path"])
        params = jsondata["params"]
        if type(params) is int:
            params = list("P_" + str(i) for i in range(params))
        self.params = params
        self.node_agents = agents
        self.extra_agents = [
            AsyncWeb3.to_checksum_address(agent)
            for agent in jsondata.get("extra_agents", [])
        ]
        self.numagents4params = jsondata["numagents4params"]
        self.version = jsondata.get("version", "0.8.19")
        self.__abi = None
        self.__bytecode = None
        self.__agents = None
        self.compiled = False

    def compile_str(self, contract: str, path: Path):
        solcx.install_solc(self.version, show_progress=True)
        solcx.set_solc_version(self.version)

        out = solcx.compile_source(
            contract, base_path=path, output_values=["abi", "bin"]
        )["<stdin>:IDS"]

        self.abi = out["abi"]
        self.bytecode = out["bin"]

    def get_agents(self):
        if not self.compiled:
            raise Exception("Contract not compiled")
        return self.agents

    def compile(self):
        if self.compiled:
            return

        self.agents = self.extra_agents + [
            agent.get_checksum_address() for agent in self.node_agents
        ]

        source: str = self.path.read_text()
        source = source.replace(
            "#AGENTS",
            ",".join(agent for agent in self.agents),
        )

        source = source.replace("#NUMAGENTS4PARAMS", str(self.numagents4params))
        source = source.replace(
            "#PARAMS", ",".join(f"'{param}'" for param in self.params)
        )

        self.compile_str(source, self.path.parent)

        self.compiled = True

    def get_abi(self):
        self.compile()
        return self.abi

    def get_bytecode(self):
        self.compile()
        return self.bytecode
