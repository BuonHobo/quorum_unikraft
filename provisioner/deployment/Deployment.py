from provisioner.quorum.Quorum import Quorum


class Deployment:
    def __init__(self, jsondata: dict):
        self.quorum = Quorum(jsondata["quorum"])
