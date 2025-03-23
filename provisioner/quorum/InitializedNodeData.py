from pathlib import Path


class InitializedNodeData:
    def __init__(
        self,
        port: str,
        address: str,
        dir: Path,
        ip: str,
        enode_hash: str,
        ws_port: str,
        raft_port: str,
    ) -> None:
        self.port = port
        self.address = address
        self.dir = dir
        self.ip = ip
        self.enode_hash = enode_hash
        self.ws_port = ws_port
        self.raft_port = raft_port

    def get_enode_url(self) -> str:
        return f"enode://{self.enode_hash}@{self.ip}:{self.port}?discport=0&raftport={self.raft_port}"

    def get_ws_url(self) -> str:
        return f"ws://{self.ip}:{self.ws_port}"