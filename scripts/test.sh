#!/bin/bash

rps=130
attempt=4
processes=3
hosts="ws://localhost:32001,ws://localhost:32002,ws://localhost:32003"
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
