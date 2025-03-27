from typing import Optional


from provisioner.quorum.contract.ContractBuilder import ContractBuilder
from provisioner.quorum.contract.DeployedContract import DeployedContract
from provisioner.quorum.node.Node import Node


class Contract:
    def __init__(
        self,
        agents: list[Node],
        jsondata: dict,
    ):
        self.builder = ContractBuilder(jsondata, agents)
        self.instance: Optional[DeployedContract] = None
        self.events: dict = jsondata.get("events", {})
        self.executions: list = jsondata.get("exec", [])

    async def deploy_using_node(self, node: "Node"):
        async with await node.connect() as w3:
            tx_hash = (
                await w3.eth.contract(
                    abi=self.builder.get_abi(), bytecode=self.builder.get_bytecode()
                )
                .constructor()
                .transact()
            )
            tx_receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
            self.instance = DeployedContract(
                tx_receipt["contractAddress"],
                self.builder.get_abi(),
                self.builder.params,
                self.builder.agents,
                self.builder.numagents4params,
            )

        await self.populate_actions(node)
        await self.execute(node)

    async def execute(self, node: "Node"):
        assert self.instance is not None
        for elem in self.executions:
            await self.instance.transact(node, elem["method"], elem["args"])

    async def populate_actions(self, node: "Node"):
        assert self.instance is not None
        states = []
        actions = []
        for state, action in self.events.items():
            states.append(state)
            actions.append(action)
        await self.instance.populate(node, states, actions)

    def get_address(self):
        assert self.instance is not None
        return self.instance.address

    def get_parameters(self):
        return self.builder.params

    def get_agents(self):
        return self.builder.agents

    def get_numagents4params(self):
        return self.builder.numagents4params

    def get_abi(self):
        return self.builder.get_abi()

    def populate(self, node: "Node", states, actions):
        assert self.instance is not None
        return self.instance.populate(node, states, actions)

    def propose(self, node: "Node", keys, values):
        assert self.instance is not None
        return self.instance.propose(node, keys, values)

    def get(self, node: "Node", key):
        assert self.instance is not None
        return self.instance.get(node, key)

    def subscribe(self, node: "Node", callback):
        assert self.instance is not None
        return self.instance.subscribe(node, callback)
