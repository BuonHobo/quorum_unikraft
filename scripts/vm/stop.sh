#!/bin/bash

source ./scripts/vm/hosts.sh
for host in ${hosts[@]}; do
    ssh $host killall geth
done