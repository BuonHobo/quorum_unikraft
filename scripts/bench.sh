#!/bin/bash

hosts="ws://192.168.2.1:32000,ws://192.168.2.2:32000"
abi=$(cat ./deployment/deployment.json | jq -rc '.abi')
address=$(cat ./deployment/deployment.json | jq -rc '.transactionReceipt.contractAddress')

python ./contractor/benchmark.py --hosts $hosts \
    --abi $abi --address $address \
    --rps 10 --duration 10