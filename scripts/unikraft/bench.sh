#!/bin/bash

hosts="ws://192.168.2.1:32000,ws://192.168.2.2:32000,ws://192.168.2.3:32000"
validators=3
members=0
processes=2
duration=10
timeout=10
size=1


for attempt in {1,2,3}; do
    for rps in {10,40,70,100,130}; do
        for consensus in {raft,qbft}; do
            ./scripts/deploy.sh $consensus $validators $members
            abi=$(cat ./deployment/deployment.json | jq -rc '.abi')
            address=$(cat ./deployment/deployment.json | jq -rc '.transactionReceipt.contractAddress')
            sleep 5
            python ./contractor/benchmark.py --hosts $hosts \
                --rps $rps --duration $duration --timeout $timeout --processes $processes \
                --output ./data/${consensus}-contract_${rps}_${attempt}.csv \
                contract --abi $abi --address $address --size $size

            ./scripts/deploy.sh $consensus $validators $members
            abi=$(cat ./deployment/deployment.json | jq -rc '.abi')
            address=$(cat ./deployment/deployment.json | jq -rc '.transactionReceipt.contractAddress')
            sleep 5
            python ./contractor/benchmark.py --hosts $hosts \
            --rps $rps --duration $duration --timeout $timeout --processes $processes \
            --output ./data/${consensus}-baseline_${rps}_${attempt}.csv 
        done
    done
done

