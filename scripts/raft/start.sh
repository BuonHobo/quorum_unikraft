#!/bin/bash

cd deployment

#Start validators
for dir in n*; do


    if [[ $(cat "$dir/role") == "member" ]]; then
        continue
    fi

    i="${dir//n}"
    ADDRESS=$(grep -o '"address": *"[^"]*"' n$i/data/keystore/accountKeystore | grep -o '"[^"]*"$' | sed 's/"//g')
    
    sudo KRAFTKIT_NO_WARN_SUDO=1 kraft run \
            --rm --detach --name n$i \
            -e PRIVATE_CONFIG=ignore \
            --network deployment:192.168.2.$i \
            -v n$i:/node -M 2Gi \
        buonhobo/geth -- /geth \
            --datadir /node/data \
            --networkid 1234 --nodiscover --verbosity 0 \
            --syncmode full --nousb \
            --raft --raftblocktime 1000 --raftport 53000 \
            --ws --ws.addr 0.0.0.0 --ws.port 32000 --ws.origins "*" \
            --ws.api admin,eth,debug,miner,net,txpool,personal,web3,raft \
            --unlock ${ADDRESS} --allow-insecure-unlock --password /node/data/keystore/accountPassword \
            --port 30303
done

#Start members
for dir in n*; do

    if [[ $(cat "$dir/role") != "member" ]]; then
        continue
    fi

    j="${dir//n}"
    enode=$(jq .[$(($j-$i-1))] members.json -rc)
    id=$(geth attach ws://192.168.2.1:32000 --exec "raft.addLearner(\"$enode\")")

    ADDRESS=$(grep -o '"address": *"[^"]*"' n$j/data/keystore/accountKeystore | grep -o '"[^"]*"$' | sed 's/"//g')
    
    sudo KRAFTKIT_NO_WARN_SUDO=1 kraft run \
            --rm --detach --name n$j \
            -e PRIVATE_CONFIG=ignore \
            --network deployment:192.168.2.$j \
            -v n$j:/node -M 1Gi \
        buonhobo/geth -- /geth \
            --datadir /node/data \
            --networkid 1234 --nodiscover --verbosity 0 --raftjoinexisting $id \
            --syncmode fast --nousb \
            --raft --raftblocktime 1000 --raftport 53000 \
            --ws --ws.addr 0.0.0.0 --ws.port 32000 --ws.origins "*" \
            --ws.api admin,eth,debug,miner,net,txpool,personal,web3,raft \
            --unlock ${ADDRESS} --allow-insecure-unlock --password /node/data/keystore/accountPassword \
            --port 30303
done
