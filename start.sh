#!/bin/bash

sudo KRAFTKIT_NO_WARN_SUDO=1 kraft net create raft --network 192.168.2.254/24

cd raft
#Start nodes
for i in $( seq 1 $NUM_NODES ); do
    ADDRESS=$(grep -o '"address": *"[^"]*"' n$i/data/keystore/accountKeystore | grep -o '"[^"]*"$' | sed 's/"//g')
    sudo KRAFTKIT_NO_WARN_SUDO=1 kraft run -p 3030$i:3030$i -p 5300$i:5300$i -p 3200$i:3200$i --network raft:192.168.2.$i \
        --name n$i -d --rm -e PRIVATE_CONFIG=ignore -v n$i:/n$i -M 2Gi buonhobo/geth -- \
        /geth --nodiscover --verbosity 6  --raft --raftblocktime 1000 --syncmode  "full"  --nousb --networkid 1234 --datadir /n$i/data \
        --raftport 5300$i --port 3030$i --unlock $ADDRESS --allow-insecure-unlock --password /n$i/data/keystore/accountPassword \
        --ws --ws.port 3200$i --ws.addr 0.0.0.0 --ws.origins "*" --ws.api admin,trace,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,raft
done
