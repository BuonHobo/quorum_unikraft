#!/bin/bash

hosts="ws://192.168.2.4:32000,ws://192.168.2.5:32000,ws://192.168.2.6:32000,ws://192.168.2.7:32000,ws://192.168.2.8:32000"



for attempt in {1,2,3}; do
    for rps in {1,20,40,60,80,100}; do
        for consensus in {raft,qbft}; do
            ./scripts/deploy.sh $consensus 3 8
            abi=$(cat ./deployment/deployment.json | jq -rc '.abi')
            address=$(cat ./deployment/deployment.json | jq -rc '.transactionReceipt.contractAddress')
            sleep 5
            python ./contractor/benchmark.py --hosts $hosts \
                --rps $rps --duration 30 --timeout 60 --processes 4 \
                --output ./data/${consensus}_contract_${rps}_${attempt}.csv \
                contract --abi $abi --address $address --size 1

            ./scripts/deploy.sh $consensus 3 8
            abi=$(cat ./deployment/deployment.json | jq -rc '.abi')
            address=$(cat ./deployment/deployment.json | jq -rc '.transactionReceipt.contractAddress')
            sleep 5
            python ./contractor/benchmark.py --hosts $hosts \
            --rps $rps --duration 30 --timeout 60 --processes 4 \
            --output ./data/${consensus}_baseline_${rps}_${attempt}.csv 
        done
    done
done

