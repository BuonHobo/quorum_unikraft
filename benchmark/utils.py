
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from web3.contract import AsyncContract
from pathlib import Path
import solcx
import asyncio


async def send(w3: AsyncWeb3, address: ChecksumAddress, value: int):
    tx_hash = await w3.eth.send_transaction({"to": address, "value": value})  # type: ignore
    tx_receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
    print(w3.to_json(tx_receipt))  # type: ignore


async def subscribe(w3: AsyncWeb3, contract: AsyncContract):
    filter = await contract.events.ActionRequired.create_filter(from_block="latest")
    while True:
        for event in await filter.get_new_entries():
            print(w3.to_json(event), flush=True)
        await asyncio.sleep(0)


async def populate(w3: AsyncWeb3, contract: AsyncContract, key, action):
    tx_hash = await contract.functions.insertMap([key], [action]).transact()
    tx_receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
    print(w3.to_json(tx_receipt))  # type: ignore


async def get(w3: AsyncWeb3, contract: AsyncContract, key):
    value = await contract.functions.statusMapDT(key).call()
    print(w3.to_json(value))


async def propose(w3: AsyncWeb3, contract: AsyncContract, key, value):
    tx_hash = await contract.functions.proposeNewValues([key], [value]).transact()
    tx_receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
    print(w3.to_json(tx_receipt))  # type: ignore


async def deploy(w3: AsyncWeb3, path: Path, params, agents):
    abi, bytecode = get_contract(path, params, agents)
    tx_hash = await w3.eth.contract(abi=abi, bytecode=bytecode).constructor().transact()
    tx_receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
    print(w3.to_json({"transactionReceipt": tx_receipt, "abi": abi}))


def install_solc(version):
    solcx.install_solc(version, show_progress=True)
    solcx.set_solc_version(version)


def compile_str(contract, path):
    install_solc("0.8.19")

    out = solcx.compile_source(contract, base_path=path, output_values=["abi", "bin"])[
        "<stdin>:IDS"
    ]
    return out


def get_contract(path: Path, params_str: str, agents_str: str):
    with path.open() as f:
        source = f.read()

    params = [f"'{param}'" for param in params_str.split(",")]
    agents = [AsyncWeb3.to_checksum_address(agent) for agent in agents_str.split(",")]
    numAgents4Params = len(agents)

    source = source.replace("%PARAMS%", f"[{','.join(params)}]")
    source = source.replace("%AGENTS%", f"[{','.join(agents)}]")
    source = source.replace("%NUMAGENTS4PARAMS%", str(numAgents4Params))

    obj = compile_str(source, path.parent)
    abi = obj["abi"]
    bytecode = obj["bin"]

    return abi, bytecode

