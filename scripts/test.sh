#!/bin/bash

rps=250
attempt=5
processes=3
hosts="ws://192.168.122.20:32000,ws://192.168.122.141:32000,ws://192.168.122.158:32000"
duration=30
timeout=30
size=1
consensus=raft
kind=contract

abi=$(cat ./deployment/deployment.json | jq -rc '.abi')
address=$(cat ./deployment/deployment.json | jq -rc '.transactionReceipt.contractAddress')

if [[ $kind == "contract" ]]; then
    python ./contractor/benchmark.py --hosts $hosts \
        --rps $rps --duration $duration --timeout $timeout --processes $processes \
        --output ./datatest/${consensus}-contract_${rps}_${attempt}.csv \
        contract --abi $abi --address $address --size $size
fi

if [[ $kind == "baseline" ]]; then
    python ./contractor/benchmark.py --hosts $hosts \
        --rps $rps --duration $duration --timeout $timeout --processes $processes \
        --output ./datatest/${consensus}-baseline_${rps}_${attempt}.csv
fi
