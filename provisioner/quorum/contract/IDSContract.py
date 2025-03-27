from typing import Coroutine, Optional


from provisioner.quorum.contract.ContractBuilder import ContractBuilder
from provisioner.quorum.contract.DeployedContract import DeployedContract
from provisioner.quorum.node.Node import Node


class Contract:
    def __init__(
        self,
        agents: list[Node],
        jsondata: dict,
    ):
        self.__builder = ContractBuilder(jsondata, agents)
        self.__instance: Optional[DeployedContract] = None
        self.__events: dict = jsondata.get("events", {})
        self.__executions: list = jsondata.get("exec", [])
        self.__subscription : Optional[Coroutine] = None

    def discard_instance(self):
        if self.__subscription is not None:
            self.__subscription.close()
        self.__instance = None
        self.__subscription = None

    async def deploy_using_node(self, node: "Node"):
        async with await node.connect() as w3:
            tx_hash = (
                await w3.eth.contract(
                    abi=self.__builder.get_abi(), bytecode=self.__builder.get_bytecode()
                )
                .constructor()
                .transact()
            )
            tx_receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
            self.__instance = DeployedContract(
                tx_receipt["contractAddress"],
                self.__builder.get_abi(),
                self.__builder.params,
                self.__builder.get_agents(),
                self.__builder.numagents4params,
            )

        await self.populate_actions(node)
        await self.execute(node)

    async def execute(self, node: "Node"):
        assert self.__instance is not None
        for elem in self.__executions:
            await self.__instance.transact(node, elem["method"], elem["args"])

    async def populate_actions(self, node: "Node"):
        assert self.__instance is not None
        states = []
        actions = []
        for state, action in self.__events.items():
            states.append(state)
            actions.append(action)
        await self.populate(node, states, actions)

    def get_address(self):
        assert self.__instance is not None
        return self.__instance.address

    def get_parameters(self):
        return self.__builder.params

    def get_agents(self):
        return self.__builder.__agents

    def get_numagents4params(self):
        return self.__builder.numagents4params

    def get_abi(self):
        return self.__builder.get_abi()

    async def populate(self, node: "Node", states, actions):
        assert self.__instance is not None
        return await self.__instance.transact(node, "insertMap", [states, actions])

    async def propose(self, node: "Node", keys, values):
        assert self.__instance is not None
        return await self.__instance.transact(node, "proposeNewValues", [keys, values])

    async def get(self, node: "Node", key):
        assert self.__instance is not None
        return await self.__instance.call(node, "statusMapDT", [key])

    def subscribe(self, node: "Node", callback):
        assert self.__instance is not None
        self.__subscription = self.__instance.subscribe(node,"ActionRequired", callback)
