from provisioner.quorum.consensus.QBFT import QBFT
from provisioner.quorum.consensus.Raft import Raft



class Quorum:
    def __init__(self, jsondata:dict):
        self.consensus = self.get_consensus(jsondata['consensus'])

    @staticmethod
    def get_consensus(jsondata: dict):
        match jsondata["name"]:
            case "raft":
                return Raft(jsondata)
            case "qbft":
                return QBFT(jsondata)
            case _:
                raise NotImplementedError(
                    f"Consensus {jsondata['name']} not implemented"
                )