#!/bin/bash

consensus=$1
num_nodes=$2

if [ -z "$consensus" ] || [ -z "$num_nodes" ]; then
    echo "Usage: $0 <consensus> <num_nodes>"
    exit 1
fi

sudo rm -rf ./deployment
mkdir deployment
cd deployment

#Initialize network
toolbox run --container ubuntu-toolbox-24.10 npx quorum-genesis-tool \
    --consensus $consensus --chainID 1337 --blockperiod 5 --requestTimeout 10 \
    --epochLength 30000 --difficulty 1 --gasLimit '0xFFFFFF' \
    --coinbase '0x0000000000000000000000000000000000000000' --validators $num_nodes \
    --members 0 --bootnodes 0 --outputPath 'artifacts'

mv artifacts/2*/* artifacts/
rmdir artifacts/2*

#Configure host IPs
for i in $( seq 1 $num_nodes ); do
    ip="192.168.2.$i"
    port="3030$i"
    raftport="5300$i"
    sed -i "0,/<HOST>/ s/<HOST>/${ip}/" artifacts/goQuorum/static-nodes.json
    sed -i "0,/:30303?/ s/30303/${port}/" artifacts/goQuorum/static-nodes.json
    sed -i "0,/&raftport=53000/ s/53000/${raftport}/" artifacts/goQuorum/static-nodes.json
    cp artifacts/goQuorum/static-nodes.json artifacts/goQuorum/permissioned-nodes.json
done

#Configure nodes
for i in $( seq 1 $num_nodes ); do
    mkdir -p n$i/data/keystore
    cp artifacts/goQuorum/permissioned-nodes.json \
        artifacts/goQuorum/static-nodes.json \
        artifacts/goQuorum/genesis.json \
        artifacts/validator$((i-1))/{nodekey*,address} \
        n$i/data/
    cp artifacts/validator$((i-1))/account* n$i/data/keystore/
done

#Initialize nodes
for i in $( seq 1 $num_nodes ); do
    cd n$i
    geth --datadir data init data/genesis.json
    cd ..
done
