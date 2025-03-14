#!/bin/bash

consensus=$1
num_validators=$2
num_members=$3

if [ -z "$consensus" ] || [ -z "$num_validators" ]; then
    echo "Usage: $0 <consensus> <num_validators> <num_members>"
    exit 1
fi

if [ -z "$num_members" ]; then
    num_members=0
fi

./scripts/stop.sh
./scripts/initialize.sh $consensus $num_validators $num_members
./scripts/net_start.sh
./scripts/${consensus}/start.sh

sleep 5

./scripts/interact.sh