import argparse
import asyncio
from pathlib import Path
from web3.providers.persistent import WebSocketProvider
from web3 import AsyncWeb3
from web3.contract import AsyncContract
from web3.middleware import ExtraDataToPOAMiddleware
from utils import deploy, send, propose, get, populate, subscribe

def main():
    global_parser = argparse.ArgumentParser(prog="contractor")
    global_parser.add_argument(
        "--host", help="Url of the host", required=True, type=str
    )
    subparsers = global_parser.add_subparsers(dest="toplevel_command")

    deploy_parser = subparsers.add_parser("deploy", help="Deploy a contract")
    deploy_parser.add_argument(
        "--contract", help="Path to the contract to deploy", required=True, type=Path
    )
    deploy_parser.add_argument(
        "--params", help="Parameters to deploy", required=True, type=str
    )
    deploy_parser.add_argument(
        "--agents", help="Agents to deploy", required=True, type=str
    )

    interact_parser = subparsers.add_parser("interact", help="Interact with a contract")
    interact_parser.add_argument(
        "--address", help="Address of the deployed contract", required=True, type=str
    )
    interact_parser.add_argument(
        "--abi", help="abi of the deployed contract", required=True, type=str
    )
    interact_subparsers = interact_parser.add_subparsers(dest="command")

    propose_parser = interact_subparsers.add_parser("propose", help="Propose a value")
    propose_parser.add_argument("--key", help="Key to propose", required=True, type=str)
    propose_parser.add_argument(
        "--value", help="Value to propose", required=True, type=int
    )

    get_parser = interact_subparsers.add_parser("get", help="Get a value")
    get_parser.add_argument("--key", help="Key to get", required=True, type=str)

    populate_parser = interact_subparsers.add_parser(
        "populate", help="Populate a contract"
    )
    populate_parser.add_argument(
        "--state", help="Key to propose", required=True, type=str
    )
    populate_parser.add_argument(
        "--action", help="Value to propose", required=True, type=str
    )

    interact_subparsers.add_parser("subscribe", help="Subscribe to a contract")

    send_parser = subparsers.add_parser("send", help="Send a transaction")
    send_parser.add_argument(
        "--address", help="Address to send to", required=True, type=str
    )
    send_parser.add_argument("--value", help="Value to send", required=True, type=int)

    asyncio.run(handle_args(global_parser.parse_args()))


async def handle_args(args):
    host: str = args.host

    async with AsyncWeb3(WebSocketProvider(host)) as w3:
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        w3.eth.default_account = (await w3.eth.accounts)[0]

        match args.toplevel_command:
            case "deploy":
                await deploy(w3, args.contract, args.params, args.agents)
            case "interact":
                await interact(w3, args)
            case "send":
                await send(w3, AsyncWeb3.to_checksum_address(args.address), args.value)
            case _:
                pass


async def interact(w3: AsyncWeb3, args):
    contract: AsyncContract = w3.eth.contract(address=args.address, abi=args.abi)
    match args.command:
        case "propose":
            await propose(w3, contract, args.key, args.value)
        case "get":
            await get(w3, contract, args.key)
        case "populate":
            await populate(w3, contract, args.state, args.action)
        case "subscribe":
            await subscribe(w3, contract)
        case _:
            pass


if __name__ == "__main__":
    main()
