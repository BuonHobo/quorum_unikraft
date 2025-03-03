#!/bin/bash

sudo KRAFTKIT_NO_WARN_SUDO=1 kraft net create raft --network 192.168.2.254/24

cd raft
#Start nodes
for i in $( seq 1 $NUM_NODES ); do
    ADDRESS=$(grep -o '"address": *"[^"]*"' n$i/data/keystore/accountKeystore | grep -o '"[^"]*"$' | sed 's/"//g')
    sudo KRAFTKIT_NO_WARN_SUDO=1 kraft run --name n$i -d --rm -e PRIVATE_CONFIG=ignore -v n$i:/n$i -M 2Gi --network raft:192.168.2.$i buonhobo/geth -- \
        /geth --nodiscover --verbosity 5  --raft --raftblocktime 1000 --syncmode  "full"  --nousb --networkid 1234 --datadir /n$i/data \
        --raftport 53000 --port 30300 --unlock $ADDRESS --allow-insecure-unlock --password /n$i/data/keystore/accountPassword \
        --ws --ws.port 32000 --ws.addr 0.0.0.0 --ws.origins "*" --ws.api admin,trace,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,raft
done
