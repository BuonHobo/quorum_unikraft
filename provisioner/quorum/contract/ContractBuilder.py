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
        self.agent_nodes = agents
        self.__agents = [
            AsyncWeb3.to_checksum_address(agent)
            for agent in jsondata.get("extra_agents", [])
        ]
        self.numagents4params = jsondata["numagents4params"]
        self.version = jsondata.get("version", "0.8.19")
        self.__abi = None
        self.__bytecode = None
        self.__compiled = False

    def compile_str(self, contract: str, path: Path):
        solcx.install_solc(self.version, show_progress=True)
        solcx.set_solc_version(self.version)

        out = solcx.compile_source(
            contract, base_path=path, output_values=["abi", "bin"]
        )["<stdin>:IDS"]

        self.__abi = out["abi"]
        self.__bytecode = out["bin"]

    def get_agents(self):
        self.compile()
        return self.__agents

    def compile(self):
        if self.__compiled:
            return

        self.__agents = self.__agents + [
            agent.get_checksum_address() for agent in self.agent_nodes
        ]

        source: str = self.path.read_text()
        source = (
            source.replace(
                "#AGENTS",
                ",".join(self.__agents),
            )
            .replace("#NUMAGENTS4PARAMS", str(self.numagents4params))
            .replace("#PARAMS", ",".join(f"'{param}'" for param in self.params))
        )

        self.compile_str(source, self.path.parent)

        self.__compiled = True

    def get_abi(self):
        self.compile()
        return self.__abi

    def get_bytecode(self):
        self.compile()
        return self.__bytecode
