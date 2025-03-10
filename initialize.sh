#!/bin/bash

sudo rm -rf ./raft
mkdir raft
cd raft

#Initialize raft network
toolbox run --container ubuntu-toolbox-24.10 npx quorum-genesis-tool --consensus raft --chainID 1337 --blockperiod 5 --requestTimeout 10 --epochLength 30000 --difficulty 1 --gasLimit '0xFFFFFF' --coinbase '0x0000000000000000000000000000000000000000' --validators $NUM_NODES --members 0 --bootnodes 0 --outputPath 'artifacts'
mv artifacts/2*/* artifacts/
rmdir artifacts/2*

#Configure host IPs
for i in $( seq 1 $NUM_NODES ); do
    ip="192.168.2.$i"
    port="3030$i"
    raftport="5300$i"
    for file in artifacts/goQuorum/{static-nodes.json,permissioned-nodes.json}; do
        sed -i "0,/<HOST>/ s/<HOST>/${ip}/" $file
        sed -i "0,/:30303?/ s/30303/${port}/" $file
        sed -i "0,/&raftport=53000/ s/53000/${raftport}/" $file
    done
done

#Configure nodes
for i in $( seq 1 $NUM_NODES ); do
    mkdir -p n$i/data/keystore
    cp artifacts/goQuorum/permissioned-nodes.json artifacts/goQuorum/static-nodes.json artifacts/goQuorum/genesis.json n$i/data/
    cp artifacts/validator$((i-1))/{nodekey*,address} n$i/data/
    cp artifacts/validator$((i-1))/account* n$i/data/keystore/
done

#Initialize nodes
for i in $( seq 1 $NUM_NODES ); do
    cd n$i
    geth --datadir data init data/genesis.json
    cd ..
done
