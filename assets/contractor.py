import argparse
import asyncio
import json
from pathlib import Path
from web3.providers.persistent import WebSocketProvider
from web3 import AsyncWeb3
from web3.contract import AsyncContract
from web3.middleware import ExtraDataToPOAMiddleware
import solcx


def main():
    global_parser = argparse.ArgumentParser(prog="contractor")
    subparsers = global_parser.add_subparsers(dest="command")
    deploy_parser = subparsers.add_parser("deploy", help="Deploy a contract")
    deploy_parser.add_argument(
        "--contract", help="Contract to deploy", required=True, type=str
    )
    deploy_parser.add_argument(
        "--host", help="Url of the host", required=True, type=str
    )
    deploy_parser.add_argument(
        "--params", help="Parameters to deploy", required=True, type=str
    )
    deploy_parser.add_argument(
        "--agents", help="Agents to deploy", required=True, type=str
    )
    propose_parser = subparsers.add_parser("propose", help="Propose a value")
    propose_parser.add_argument(
        "--key", help="Key to propose", required=True, type=str)
    propose_parser.add_argument(
        "--value", help="Value to propose", required=True, type=int
    )
    propose_parser.add_argument(
        "--address", help="Address of the deployed contract", required=True, type=str
    )
    propose_parser.add_argument(
        "--abi", help="abi of the deployed contract", required=True, type=str
    )
    propose_parser.add_argument(
        "--host", help="Url of the host", required=True, type=str
    )
    get_parser = subparsers.add_parser("get", help="Get a value")
    get_parser.add_argument(
        "--key", help="Key to get", required=True, type=str)
    get_parser.add_argument(
        "--address", help="Address of the deployed contract", required=True, type=str
    )
    get_parser.add_argument(
        "--abi", help="abi of the deployed contract", required=True, type=str
    )
    get_parser.add_argument(
        "--host", help="Url of the host", required=True, type=str
    )
    compile_parser = subparsers.add_parser(
        "compile", help="Compile a contract")
    compile_parser.add_argument(
        "--contract", help="Contract to compile", required=True, type=str
    )
    populate_parser = subparsers.add_parser(
        "populate", help="Populate a contract"
    )
    populate_parser.add_argument(
        "--key", help="Key to propose", required=True, type=str)
    populate_parser.add_argument(
        "--action", help="Value to propose", required=True, type=str
    )
    populate_parser.add_argument(
        "--address", help="Address of the deployed contract", required=True, type=str
    )
    populate_parser.add_argument(
        "--abi", help="abi of the deployed contract", required=True, type=str
    )
    populate_parser.add_argument(
        "--host", help="Url of the host", required=True, type=str
    )
    subscribe_parser = subparsers.add_parser(
        "subscribe", help="Subscribe to a contract"
    )
    subscribe_parser.add_argument(
        "--address", help="Address of the deployed contract", required=True, type=str
    )
    subscribe_parser.add_argument(
        "--abi", help="abi of the deployed contract", required=True, type=str
    )
    subscribe_parser.add_argument(
        "--host", help="Url of the host", required=True, type=str
    )


    args = global_parser.parse_args()
    match args.command:
        case "deploy":
            asyncio.run(deploy(args.host, Path(
                args.contract), args.params, args.agents))
        case "propose":
            asyncio.run(propose(args.host, args.abi,
                        args.address, args.key, args.value))
        case "get":
            asyncio.run(get(args.host, args.abi, args.address, args.key))
        case "compile":
            abi, bin = compile(args.contract)
            print(json.dumps({"abi": abi, "bin": bin}, separators=(',', ':')))
        case "populate":
            asyncio.run(populate(args.host, args.abi,
                        args.address, args.key, args.action))
        case "subscribe":
            asyncio.run(subscribe(args.host ,args.address, args.abi))

async def subscribe(host, address, abi):
    async with AsyncWeb3(WebSocketProvider(host)) as w3:
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        w3.eth.default_account = (await w3.eth.accounts)[0]
        contract = w3.eth.contract(address=address, abi=abi)
        event_filter = await contract.events.ActionRequired.create_filter(from_block='latest')
        while True:
            for event in await event_filter.get_new_entries():
                print(json.dumps(event, separators=(',', ':')))
            await asyncio.sleep(1)

async def populate(host, abi, address, key, action):
    async with AsyncWeb3(WebSocketProvider(host)) as w3:
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        w3.eth.default_account = (await w3.eth.accounts)[0]
        contract = w3.eth.contract(address=address, abi=abi)
        tx_hash = await contract.functions.insertMap([key], [action]).transact()
        tx_receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
        print(json.dumps(
            {'tx_rcpt': tx_receipt.transactionHash.hex()}, separators=(',', ':')))


async def get(host, abi, address, key):
    async with AsyncWeb3(WebSocketProvider(host)) as w3:
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        w3.eth.default_account = (await w3.eth.accounts)[0]
        contract = w3.eth.contract(address=address, abi=abi)
        value = await contract.functions.statusMapDT(key).call()
        print(json.dumps({"value": value}, separators=(',', ':')))


async def propose(host, abi, address, key, value):
    async with AsyncWeb3(WebSocketProvider(host)) as w3:
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        w3.eth.default_account = (await w3.eth.accounts)[0]
        contract = w3.eth.contract(address=address, abi=abi)
        tx_hash = await contract.functions.proposeNewValues([key], [value]).transact()
        tx_receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
        print(json.dumps(
            {'tx_rcpt': tx_receipt.transactionHash.hex()}, separators=(',', ':')))


async def deploy(host, path, params, agents):
    with path.open() as f:
        source = f.read()

    params = params.split(",")
    params = [f"'{param}'" for param in params]
    agents = agents.split(",")
    agents = [AsyncWeb3.to_checksum_address(agent) for agent in agents]
    numAgents4Params = len(agents)//2+1

    source = source.replace("%PARAMS%", f"[{','.join(params)}]")
    source = source.replace("%AGENTS%", f"[{','.join(agents)}]")
    source = source.replace("%NUMAGENTS4PARAMS%", str(numAgents4Params))

    abi, bytecode = compile_str(source, path.parent)

    async with AsyncWeb3(WebSocketProvider(host)) as w3:
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        w3.eth.default_account = (await w3.eth.accounts)[0]
        tx_hash = await w3.eth.contract(abi=abi, bytecode=bytecode).constructor().transact()
        tx_receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
        print(json.dumps(
            {"address": tx_receipt.contractAddress, "abi": abi}, separators=(',', ':')))


def install_solc(version):
    solcx.install_solc(version, show_progress=True)
    solcx.set_solc_version(version)


def compile_str(contract, path):
    install_solc("0.8.19")

    out = solcx.compile_source(contract, base_path=path, output_values=[
                               "abi", "bin"])["<stdin>:IDS"]
    return out["abi"], out["bin"]


def compile(path):
    install_solc("0.8.19")

    out = solcx.compile_files([path], output_values=[
                              "abi", "bin"])[path+':IDS']
    return out["abi"], out["bin"]


if __name__ == "__main__":
    main()
