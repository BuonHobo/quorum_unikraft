import argparse
from logger import Logger
from web3.providers.persistent import WebSocketProvider
from web3 import AsyncWeb3
import asyncio

def main():
    global_parser = argparse.ArgumentParser(prog="benchmark")
    global_parser.add_argument(
        "--hosts", help="Comma separated list of host urls", required=True, type=str
    )
    global_parser.add_argument(
        "--rps", help="Requests per second", required=True, type=int
    )
    global_parser.add_argument(
        "--duration", help="Duration of the benchmark", required=True, type=int
    )
    global_parser.add_argument(
        "--abi", help="ABI of the deployed contract", required=True, type=str
    )
    global_parser.add_argument(
        "--address", help="Address of the deployed contract", required=True, type=str
    )

    args = global_parser.parse_args()
    hosts = args.hosts.split(",")
    rps = args.rps
    duration = args.duration
    contract_abi = args.abi
    contract_address = args.address

    host_to_rps = distribute_rps(hosts, rps)
    host_to_w3 = initialize_connections(hosts)
    logger = Logger()
    
    for host,w3 in host_to_w3.items():
        logger.schedule_log(f"Connesso a {host}: {w3}")
    asyncio.run(logger.log())


    
def distribute_rps(hosts, rps):
    host_to_rps = {}
    leftover_rps = rps
    while leftover_rps > 0:
        for host in hosts:
            host_rps = min(rps // len(hosts), leftover_rps)
            leftover_rps -= host_rps
            host_to_rps[host] = host_rps
    return host_to_rps

def initialize_connections(hosts):
    host_to_w3 = {}
    for host in hosts:
        w3 = AsyncWeb3(WebSocketProvider(host))
        host_to_w3[host] = w3

    asyncio.run(connect_to_hosts(host_to_w3))
    return host_to_w3

async def connect_to_hosts(host_to_w3):
    await asyncio.gather(*[w3.provider.connect() for w3 in host_to_w3.values()])

if __name__=="__main__":
    main()