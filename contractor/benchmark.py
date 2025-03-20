import argparse
from multiprocessing import cpu_count
from pathlib import Path


from model.strategies.NodeMoneyStrategy import NodeMoneyStrategy
from model.strategies.NodeContractStrategy import NodeContractStrategy
from model.workers.Worker import Worker
from model.Benchmark import Benchmark
from model.strategies.ContractStrategy import ContractStrategy
from model.strategies.MoneyStrategy import MoneyStrategy


def entrypoint():
    global barrier

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
        "--output", help="Log the transactions", required=True, type=Path
    )
    global_parser.add_argument(
        "--processes",
        help="Number of processes",
        required=False,
        type=int,
        default=cpu_count(),
    )
    global_parser.add_argument(
        "--timeout",
        help="Timeout for the transactions",
        required=False,
        type=int,
        default=30,
    )
    global_parser.add_argument(
        "--local",
        help="Whether to sign the transactions locally",
        required=False,
        action="store_true",
        default=False,
    )
    subparser = global_parser.add_subparsers(title="type", dest="type")
    contract_parser = subparser.add_parser("contract")
    contract_parser.add_argument(
        "--address", help="Address of the deployed contract", type=str
    )
    contract_parser.add_argument("--abi", help="ABI of the deployed contract", type=str)

    args = global_parser.parse_args()
    hosts = args.hosts.split(",")
    rps = args.rps
    duration = args.duration
    output = args.output
    processes = args.processes
    timeout = args.timeout

    if args.local:
        if args.type == "contract":
            strategy = ContractStrategy(args.address, args.abi)
        else:
            strategy = MoneyStrategy()
    else:
        if args.type == "contract":
            strategy = NodeContractStrategy(args.address, args.abi, hosts)
        else:
            strategy = NodeMoneyStrategy(hosts)

    Benchmark(
        hosts, rps, duration, output, processes, timeout, strategy, Worker
    ).start()


if __name__ == "__main__":
    entrypoint()
