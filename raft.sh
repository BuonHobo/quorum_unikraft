#!/bin/bash

n=2

#Delete all
sudo KRAFTKIT_NO_WARN_SUDO=1 kraft rm --all
sudo KRAFTKIT_NO_WARN_SUDO=1 kraft net remove raft
sudo rm -rf raft

sudo KRAFTKIT_NO_WARN_SUDO=1 kraft net create raft --network 192.168.2.254/24
mkdir raft
cd raft

#Initialize raft network
toolbox run npx quorum-genesis-tool --consensus raft --chainID 1337 --blockperiod 5 --requestTimeout 10 --epochLength 30000 --difficulty 1 --gasLimit '0xFFFFFF' --coinbase '0x0000000000000000000000000000000000000000' --validators $n --members 0 --bootnodes 0 --outputPath 'artifacts'
mv artifacts/2*/* artifacts/
rmdir artifacts/2*

#Configure host IPs
for i in $( seq 1 $n ); do
    ip="192.168.2.$i"
    sed -i "0,/<HOST>/ s/<HOST>/${ip}/" artifacts/goQuorum/static-nodes.json
done

#Configure nodes
for i in $( seq 1 $n ); do
    mkdir -p n$i/data/keystore
    cp artifacts/goQuorum/static-nodes.json artifacts/goQuorum/genesis.json n$i/data/
    cp artifacts/validator$((i-1))/{nodekey*,address} n$i/data/
    cp artifacts/validator$((i-1))/account* n$i/data/keystore/
done

#Initialize nodes
for i in $( seq 1 $n ); do
    cd n$i
    geth --datadir data init data/genesis.json
    cd ..
done

#Start nodes
for i in $( seq 1 $n ); do
    ADDRESS=$(grep -o '"address": *"[^"]*"' n$i/data/keystore/accountKeystore | grep -o '"[^"]*"$' | sed 's/"//g')
    sudo KRAFTKIT_NO_WARN_SUDO=1 kraft run --name n$i -d --rm -e PRIVATE_CONFIG=ignore -v n$i:/n$i -M 2Gi --network raft:192.168.2.$i buonhobo/geth -- \
        /geth --nodiscover --verbosity 5  --raft --raftblocktime 1000 --syncmode  "full"  --nousb --networkid 1234 --datadir /n$i/data \
        --raftport 53000 --port 30300 --unlock $ADDRESS --allow-insecure-unlock --password /n$i/data/keystore/accountPassword \
        --ws --ws.port 32000 --ws.addr 0.0.0.0 --ws.origins "*" --ws.api admin,trace,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,raft
done
