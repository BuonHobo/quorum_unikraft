#!/bin/bash

tech=$1
consensus=$2
num_validators=$3
num_members=$4

if [ -z "$consensus" ] || [ -z "$num_validators" ]; then
    echo "Usage: $0 <consensus> <num_validators> <num_members>"
    exit 1
fi

if [ -z "$num_members" ]; then
    num_members=0
fi

./scripts/${tech}/stop.sh
./scripts/${tech}/initialize.sh $consensus $num_validators $num_members
./scripts/${tech}/${consensus}/start.sh

sleep 5

./scripts/interact.sh $(cat deployment/host)