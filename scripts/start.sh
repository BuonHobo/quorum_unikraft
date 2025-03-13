#!/bin/bash

num_nodes=$1
consensus=$2

if [ -z "$num_nodes" ] || [ -z "$consensus" ]; then
    echo "Usage: $0 <num_nodes> <consensus>"
    exit 1
fi

./scripts/stop.sh
./scripts/initialize.sh $consensus $num_nodes
./scripts/net_start.sh
./scripts/${consensus}_start.sh $num_nodes

sleep 5

./scripts/interact.sh