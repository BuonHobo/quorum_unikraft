#!/bin/bash

hosts="ws://192.168.2.1:32000,ws://192.168.2.2:32000,ws://192.168.2.3:32000"
abi=$(cat ./deployment/deployment.json | jq -rc '.abi')
address=$(cat ./deployment/deployment.json | jq -rc '.transactionReceipt.contractAddress')

rm -rf out

python ./contractor/benchmark.py --hosts $hosts \
    --rps 10 --duration 10 --timeout 120 --processes 4 \
    --output ./out.csv \
    contract --abi $abi --address $address \