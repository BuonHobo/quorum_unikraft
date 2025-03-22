#!/bin/bash

rps=130
attempt=3
processes=3
hosts="ws://192.168.2.1:32000,ws://192.168.2.2:32000,ws://192.168.2.3:32000"
duration=30
timeout=60
size=1
consensus=raft
kind=contract

./scripts/deploy.sh $consensus 3
abi=$(cat ./deployment/deployment.json | jq -rc '.abi')
address=$(cat ./deployment/deployment.json | jq -rc '.transactionReceipt.contractAddress')
sleep 5

if [[ $kind == "contract" ]]; then
    python ./contractor/benchmark.py --hosts $hosts \
        --rps $rps --duration $duration --timeout $timeout --processes $processes \
        --output ./data/test/${consensus}-contract_${rps}_${attempt}.csv \
        contract --abi $abi --address $address --size $size
fi

if [[ $kind == "baseline" ]]; then
    python ./contractor/benchmark.py --hosts $hosts \
        --rps $rps --duration $duration --timeout $timeout --processes $processes \
        --output ./data/test/${consensus}-baseline_${rps}_${attempt}.csv
fi
