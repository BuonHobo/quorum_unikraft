import importlib
from provisioner.quorum.node.Node import Node

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provisioner.quorum.Quorum import Quorum


class Consensus:
    async def start(self, quorum: "Quorum"):
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_static_nodes(self, nodes: list[Node]) -> list[Node]:
        raise NotImplementedError("This method must be implemented by the subclass")

    def __init__(self, jsondata: dict):
        self.name: str = jsondata["consensus"]

    @staticmethod
    def get_consensus(jsondata: dict):
        name = str(jsondata["consensus"]).capitalize()
        module = importlib.import_module("provisioner.quorum.consensus." + name)
        consensus = getattr(module, name)
        return consensus(jsondata)
