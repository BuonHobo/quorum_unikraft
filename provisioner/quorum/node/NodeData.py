from pathlib import Path


class ConnData:
    def __init__(self, ip: str, port: int, ws_port: int, raft_port: int):
        self.ip = ip
        self.port = port
        self.ws_port = ws_port
        self.raft_port = raft_port

    def get_ws_url(self) -> str:
        return f"ws://{self.ip}:{self.ws_port}"


class NodeData:
    def __init__(
        self,
        address: str,
        dir: Path,
        enode_hash: str,
        connection_data: ConnData,
    ) -> None:
        self.address = address
        self.dir = dir
        self.enode_hash = enode_hash
        self.connection_data = connection_data

    def get_enode_url(self) -> str:
        return f"enode://{self.enode_hash}@{self.connection_data.ip}:{self.connection_data.port}?discport=0&raftport={self.connection_data.raft_port}"
