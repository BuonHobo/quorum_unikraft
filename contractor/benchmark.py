import argparse
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Barrier, Process, Queue, cpu_count
from pathlib import Path
from random import choice, randint
import signal


from web3.providers.persistent import WebSocketProvider
from web3 import AsyncWeb3
import asyncio
from web3.middleware import ExtraDataToPOAMiddleware
from web3.contract import AsyncContract
from time import time


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
        "--abi", help="ABI of the deployed contract", required=True, type=str
    )
    global_parser.add_argument(
        "--address", help="Address of the deployed contract", required=True, type=str
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

    args = global_parser.parse_args()
    hosts = args.hosts.split(",")
    rps = args.rps
    duration = args.duration
    contract_abi = args.abi
    contract_address = args.address
    output = args.output
    processes = args.processes
    barrier = Barrier(processes)
    timeout = args.timeout

    asyncio.run(
        main(
            hosts,
            rps,
            duration,
            contract_abi,
            contract_address,
            output,
            processes,
            timeout,
        )
    )


async def main(hosts, rps, duration, abi, address, output, processes, timeout):
    logger = Process(target=log, args=(output, time()))
    logger.start()
    with ProcessPoolExecutor(processes) as executor:
        await asyncio.gather(
            *[
                asyncio.get_running_loop().run_in_executor(
                    executor,
                    process_wrapper,
                    hosts,
                    rps,
                    processes,
                    duration,
                    abi,
                    address,
                    i,
                    timeout,
                )
                for i in range(processes)
            ]
        )
        logger.terminate()


def log(output, start_time):
    signal.signal(signal.SIGTERM, handler=lambda x, y: exit(0))
    id = 0
    with output.open("w") as f:
        f.write("id,pid,host,nonce,sent_time,time_to_send,time_to_rcpt,recv_time\n")
        while True:
            pid, host, nonce, start, send, rcpt = log_queue.get()
            f.write(
                f"{id},{pid},{host},{nonce},{start - start_time:.3f},{send - start:.3f},{rcpt - send:.3f},{rcpt - start_time:.3f}\n"
            )
            id += 1
            f.flush()


def process_wrapper(hosts, rps, processes, duration, abi, address, i, timeout):
    asyncio.run(process(hosts, rps, processes, duration, abi, address, i, timeout))


async def fund_account(connector, address, amount):
    tx_hash = await connector.eth.send_transaction(
        {
            "from": connector.eth.default_account,
            "to": address,
            "value": amount,
            "gas": 25_000_000,
            "gasPrice": 0,
            "chainId": 1337,
        }  # type: ignore
    )
    await connector.eth.wait_for_transaction_receipt(tx_hash)


async def initialize_connector(connector):
    await connector.provider.connect()
    connector.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    connector.eth.default_account = (await connector.eth.accounts)[0]


async def process(hosts, rps, processes, duration, abi, address, pid, timeout):
    connectors = [AsyncWeb3(WebSocketProvider(host)) for host in hosts]
    contracts = [
        connector.eth.contract(address=address, abi=abi) for connector in connectors
    ]
    account = choice(connectors).eth.account.create()

    await asyncio.gather(*[initialize_connector(connector) for connector in connectors])
    await fund_account(choice(connectors), account.address, duration * rps * 2)

    nonce = 0
    async with asyncio.TaskGroup() as g:
        offset = 1 / rps * pid
        barrier.wait()
        await asyncio.sleep(offset)
        t_start = time()
        while time() - t_start < duration + offset:
            host = randint(0, len(hosts) - 1)
            connector = connectors[host]

            g.create_task(
                send_transaction(
                    connector, nonce, pid, host, account.address, account.key, timeout
                )
            )

            # contract = contracts[host]
            # g.create_task(
            #     transact_contract(
            #         connector,
            #         contract,
            #         nonce,
            #         pid,
            #         host,
            #         account.address,
            #         account.key,
            #         timeout,
            #     )
            # )
            nonce += 1
            await asyncio.sleep(1 / rps * processes)

    await asyncio.gather(*[connector.provider.disconnect() for connector in connectors])


async def transact_contract(
    connector: AsyncWeb3,
    contract: AsyncContract,
    nonce: int,
    id: int,
    host: int,
    address,
    key,
    timeout: int,
):
    try:
        time_start = time()
        tx = await contract.functions.proposeNewValues(
            ["P0"], [nonce]
        ).build_transaction(
            {"nonce": nonce, "gasPrice": 0, "from": address, "gas": 25000000}  # type: ignore
        )
        signed_tx = connector.eth.account.sign_transaction(tx, private_key=key)
        tx_hash = await connector.eth.send_raw_transaction(signed_tx.raw_transaction)
        time_send = time()
        await connector.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        time_rcpt = time()
        log_queue.put((id, host, nonce, time_start, time_send, time_rcpt))
    except Exception as e:
        print(
            f"Exception on pid {id}: Transaction {nonce} on host {host} failed with error: {e}"
        )


async def send_transaction(
    connector: AsyncWeb3,
    nonce: int,
    id: int,
    host: int,
    address,
    key,
    timeout: int,
):
    try:
        time_start = time()
        tx = {
            "to": connector.eth.default_account,
            "from": address,
            "value": 1,
            "gas": 25_000_000,
            "nonce": nonce,
            "gasPrice": 0,
            "chainId": 1337,
        }
        signed_tx = connector.eth.account.sign_transaction(tx, private_key=key)
        tx_hash = await connector.eth.send_raw_transaction(signed_tx.raw_transaction)  # type: ignore
        time_send = time()
        await connector.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        time_rcpt = time()
        log_queue.put((id, host, nonce, time_start, time_send, time_rcpt))
    except Exception as e:
        print(
            f"Exception on pid {id}: Transaction {nonce} on host {host} failed with error: {e}"
        )


if __name__ == "__main__":
    log_queue = Queue()
    barrier: Barrier = None  # type: ignore
    entrypoint()
