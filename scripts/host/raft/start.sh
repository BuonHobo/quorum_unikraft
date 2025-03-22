#!/bin/bash

cd deployment

#Start validators
for dir in n*; do


    if [[ $(cat "$dir/role") == "member" ]]; then
        continue
    fi

    i="${dir//n}"
    ADDRESS=$(grep -o '"address": *"[^"]*"' n$i/data/keystore/accountKeystore | grep -o '"[^"]*"$' | sed 's/"//g')
    
    geth \
        --datadir n$i/data \
        --networkid 1234 --nodiscover --verbosity 0 \
        --syncmode full --nousb \
        --raft --raftblocktime 1000 --raftport 5300$i \
        --ws --ws.addr 0.0.0.0 --ws.port 3200$i --ws.origins "*" \
        --ws.api admin,eth,debug,miner,net,txpool,personal,web3,raft \
        --unlock ${ADDRESS} --allow-insecure-unlock --password n$i/data/keystore/accountPassword \
        --port 3030$i \
        &>/dev/null &
done

sleep 5

#Start members
for dir in n*; do

    if [[ $(cat "$dir/role") != "member" ]]; then
        continue
    fi

    j="${dir//n}"
    enode=$(jq .[$(($j-$i-1))] members.json -rc)
    echo enode is $enode
    id=$(geth attach ws://127.0.0.1:32001 --exec "raft.addLearner(\"$enode\")")

    ADDRESS=$(grep -o '"address": *"[^"]*"' n$j/data/keystore/accountKeystore | grep -o '"[^"]*"$' | sed 's/"//g')
    

    PRIVATE_CONFIG=ignore geth \
        --datadir n$j/data \
        --networkid 1234 --nodiscover --verbosity 0 --raftjoinexisting $id \
        --syncmode full --nousb \
        --raft --raftblocktime 1000 --raftport 5300$j \
        --ws --ws.addr 0.0.0.0 --ws.port 3200$j --ws.origins "*" \
        --ws.api admin,eth,debug,miner,net,txpool,personal,web3,raft \
        --unlock ${ADDRESS} --allow-insecure-unlock --password n$j/data/keystore/accountPassword \
        --port 3030$j \
        &>/dev/null &
done
