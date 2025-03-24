from provinew.quorum.consensus.Consensus import Consensus


class Quorum:
    def __init__(self, jsondata: dict):
        self.consensus: Consensus = Consensus.get_consensus(jsondata["consensus"])
