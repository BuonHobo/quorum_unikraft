#!/bin/bash
NUM_NODES=3
export NUM_NODES

./stop.sh
./initialize.sh
./start.sh

sleep 5

params="P1,P2"
agent=$(cat ./raft/n1/data/keystore/accountAddress)
host="ws://192.168.2.1:32000"
ct_path="./contracts/IDS.sol"

python ./contractor.py --host $host \
    deploy --contract $ct_path --params $params --agents $agent \
    > ./raft/deployment.json

abi=$(cat ./raft/deployment.json | jq -rc '.abi')
address=$(cat ./raft/deployment.json | jq -rc '.transactionReceipt.contractAddress')

python ./contractor.py --host $host \
    interact --abi $abi --address $address \
    populate --key 12 --action ciao

python ./contractor.py --host $host \
    interact --abi $abi --address $address \
    subscribe > ./raft/events.txt &

python ./contractor.py --host $host \
    interact --abi $abi --address $address \
    propose --key P1 --value 1

python ./contractor.py --host ws://192.168.2.2:32000 \
    interact --abi $abi --address $address \
    propose --key P2 --value 2

python ./contractor.py --host ws://192.168.2.2:32000 \
    send --address $agent --value 10

python ./contractor.py --host $host \
    interact --abi $abi --address $address \
    get --key P1