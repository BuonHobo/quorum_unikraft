#!/bin/bash

consensus=$1
num_validators=$2
num_members=$3


if [ -z "$consensus" ] || [ -z "$num_validators" ] || [ -z "$num_members" ]; then
    echo "Usage: $0 <consensus> <num_validators> <num_members>"
    exit 1
fi

sudo rm -rf ./deployment
mkdir deployment
cd deployment

#Generate node data
toolbox run --container ubuntu-toolbox-24.10 npx quorum-genesis-tool \
    --consensus $consensus --chainID 1337 --blockperiod 5 --requestTimeout 10 \
    --epochLength 30000 --difficulty 1 --gasLimit '0xFFFFFF' \
    --coinbase '0x0000000000000000000000000000000000000000' --validators $num_validators \
    --members $num_members --bootnodes 0 --outputPath 'artifacts'

mv artifacts/2*/* artifacts/
rmdir artifacts/2*

#Configure enode urls
for i in $( seq 1 $(($num_validators + $num_members)) ); do
    ip="192.168.2.$i"
    sed -i "0,/<HOST>/ s/<HOST>/${ip}/" artifacts/goQuorum/static-nodes.json
done

# If consensus is raft, split validators and members. Raft needs the members to be added later as learners
if [[ $consensus == "raft" ]]; then
    jq .[0:${num_validators}] artifacts/goQuorum/static-nodes.json > validators.json
    jq .[${num_validators}:$(($num_members+$num_validators))] artifacts/goQuorum/static-nodes.json > members.json
    cp validators.json artifacts/goQuorum/static-nodes.json
fi

cp artifacts/goQuorum/static-nodes.json artifacts/goQuorum/permissioned-nodes.json

#Configure validators
for i in $( seq 1 $num_validators ); do
    mkdir -p n$i/data/keystore
    cp artifacts/goQuorum/permissioned-nodes.json \
        artifacts/goQuorum/static-nodes.json \
        artifacts/goQuorum/genesis.json \
        artifacts/validator$((i-1))/{nodekey*,address} \
        n$i/data/
    cp artifacts/validator$((i-1))/account* n$i/data/keystore/
    echo validator > n$i/role
done

#Configure members
for i in $( seq 1 $num_members ); do
    j=$(($i + $num_validators))
    mkdir -p n$j/data/keystore
    cp artifacts/goQuorum/permissioned-nodes.json \
        artifacts/goQuorum/static-nodes.json \
        artifacts/goQuorum/genesis.json \
        artifacts/member$((i-1))/{nodekey*,address} \
        n$j/data/
    cp artifacts/member$((i-1))/account* n$j/data/keystore/
    echo member > n$j/role
done

#Initialize nodes
for i in $( seq 1 $(($num_validators + $num_members)) ); do
    cd n$i
    geth --datadir data init data/genesis.json
    cd ..
done
