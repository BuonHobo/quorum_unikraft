#!/bin/bash

rps=100
attempt=6
processes=3
hosts=""
for node in deployment/n*; do
    ip=$(cat $node/wsurl)
    if [[ -z "$hosts" ]]; then
        hosts="$ip"
        host="$ip"
    else
        hosts="$hosts,$ip"
    fi
done
duration=30
timeout=30
size=1
consensus=raft
kind=contract

./scripts/interact.sh $host

abi=$(cat ./deployment/deployment.json | jq -rc '.abi')
address=$(cat ./deployment/deployment.json | jq -rc '.transactionReceipt.contractAddress')

if [[ $kind == "contract" ]]; then
    python ./benchmark/benchmark.py --hosts $hosts \
        --rps $rps --duration $duration --timeout $timeout --processes $processes \
        --output ./datatest/${consensus}-contract_${rps}_${attempt}.csv \
        contract --abi $abi --address $address --size $size
fi

if [[ $kind == "baseline" ]]; then
    python ./benchmark/benchmark.py --hosts $hosts \
        --rps $rps --duration $duration --timeout $timeout --processes $processes \
        --output ./datatest/${consensus}-baseline_${rps}_${attempt}.csv
fi
