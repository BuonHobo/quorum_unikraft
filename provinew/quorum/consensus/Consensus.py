import importlib
from provinew.quorum.node.Node import Node

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provinew.quorum.Quorum import Quorum


class Consensus:
    async def start(self, quorum: "Quorum"):
        raise NotImplementedError("This method must be implemented by the subclass")

    def get_static_nodes(self, quorum: "Quorum") -> list[Node]:
        raise NotImplementedError("This method must be implemented by the subclass")

    def __init__(self, jsondata: dict):
        self.name: str = jsondata["name"]

    @staticmethod
    def get_consensus(jsondata: dict):
        name = str(jsondata["name"]).capitalize()
        module = importlib.import_module("provinew.quorum.consensus." + name)
        consensus = getattr(module, name)
        return consensus(jsondata)
