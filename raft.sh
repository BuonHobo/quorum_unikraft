#!/bin/bash
NUM_NODES=3
export NUM_NODES

./stop.sh
./initialize.sh
./start.sh

sleep 5

params="P1,P2"
agent=$(cat raft/n1/data/keystore/accountAddress)
host="ws://192.168.2.1:32000"
ct_path="assets/contracts/IDS.sol"

python assets/contractor.py deploy \
    --host $host \
    --contract $ct_path \
    --params $params --agents $agent \
    > deployment.json

abi=$(cat deployment.json | jq -rc '.abi')
address=$(cat deployment.json | jq -rc '.address')

python assets/contractor.py populate \
    --host $host \
    --abi $abi \
    --address $address \
    --key P1 --action test

python assets/contractor.py subscribe \
    --host $host \
    --abi $abi \
    --address $address > events.txt &

python assets/contractor.py propose \
    --host $host \
    --abi $abi \
    --address $address \
    --key P1 --value 10

python assets/contractor.py propose \
    --host ws://192.168.2.2:32000 \
    --abi $abi \
    --address $address \
    --key P1 --value 10

python assets/contractor.py get \
    --host $host \
    --abi $abi \
    --address $address \
    --key P1