#!/bin/bash

source ./scripts/vm/hosts.sh
cd deployment

#Start validators
for dir in n*; do


    if [[ $(cat "$dir/role") == "member" ]]; then
        continue
    fi

    i="${dir//n}"
    ADDRESS=$(grep -o '"address": *"[^"]*"' n$i/data/keystore/accountKeystore | grep -o '"[^"]*"$' | sed 's/"//g')
    
    ssh ${hosts[$((i-1))]} PRIVATE_CONFIG=ignore geth \
        --datadir node/data \
        --networkid 1234 --nodiscover --verbosity 0 \
        --syncmode full --nousb \
        --raft --raftblocktime 1000 --raftport 53000 \
        --ws --ws.addr 0.0.0.0 --ws.port 32000 --ws.origins "*" \
        --ws.api admin,eth,debug,miner,net,txpool,personal,web3,raft \
        --unlock ${ADDRESS} --allow-insecure-unlock --password node/data/keystore/accountPassword \
        --port 30303 \
        &>/dev/null &
done

sleep 10

#Start members
for dir in n*; do

    if [[ $(cat "$dir/role") != "member" ]]; then
        continue
    fi

    j="${dir//n}"
    enode=$(jq .[$(($j-$i-1))] members.json -rc)
    echo enode is $enode
    id=$(geth attach $(cat host) --exec "raft.addLearner(\"$enode\")")

    ADDRESS=$(grep -o '"address": *"[^"]*"' n$j/data/keystore/accountKeystore | grep -o '"[^"]*"$' | sed 's/"//g')
    

    ssh ${hosts[$((j-1))]} PRIVATE_CONFIG=ignore geth \
        --datadir node/data \
        --networkid 1234 --nodiscover --verbosity 0 --raftjoinexisting $id\
        --syncmode full --nousb \
        --raft --raftblocktime 1000 --raftport 53000 \
        --ws --ws.addr 0.0.0.0 --ws.port 32000 --ws.origins "*" \
        --ws.api admin,eth,debug,miner,net,txpool,personal,web3,raft \
        --unlock ${ADDRESS} --allow-insecure-unlock --password node/data/keystore/accountPassword \
        --port 30303 \
        &>/dev/null &
done
