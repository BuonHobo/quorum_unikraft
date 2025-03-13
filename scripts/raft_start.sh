#!/bin/bash

num_nodes=$1

if [ -z "$num_nodes" ]; then
    echo "Usage: $0 <consensus> <num_nodes>"
    exit 1
fi

cd deployment
#Start nodes
for i in $( seq 1 $num_nodes ); do
    ADDRESS=$(grep -o '"address": *"[^"]*"' n$i/data/keystore/accountKeystore | grep -o '"[^"]*"$' | sed 's/"//g')
    sudo KRAFTKIT_NO_WARN_SUDO=1 kraft run \
            --rm --detach --name n$i \
            -e PRIVATE_CONFIG=ignore \
            --network deployment:192.168.2.$i \
            -v n$i:/n$i -M 1Gi \
        buonhobo/geth -- /geth \
            --datadir /n$i/data \
            --networkid 1234 --nodiscover --verbosity 5 \
            --syncmode full --nousb \
            --raft --raftblocktime 1000 --raftport 5300$i \
            --ws --ws.addr 0.0.0.0 --ws.port 32000 --ws.origins "*" \
            --ws.api admin,eth,debug,miner,net,txpool,personal,web3,istanbul \
            --unlock ${ADDRESS} --allow-insecure-unlock --password /n$i/data/keystore/accountPassword \
            --port 3030$i
done
