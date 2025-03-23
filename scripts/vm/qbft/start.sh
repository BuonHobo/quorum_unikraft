#!/bin/bash

source ./scripts/vm/hosts.sh
cd deployment

for dir in n*; do
    i="${dir//n}"
    ADDRESS=$(grep -o '"address": *"[^"]*"' n$i/data/keystore/accountKeystore | grep -o '"[^"]*"$' | sed 's/"//g')

    val=""
    if grep -q "validator" n$i/role; then
        val="--istanbul.blockperiod 1 --mine --miner.threads 1 --miner.gasprice 0 --emitcheckpoints"
    fi

    ssh ${hosts[$((i-1))]} PRIVATE_CONFIG=ignore geth \
        --datadir node/data \
        --networkid 1234 --nodiscover --verbosity 0 \
        --syncmode full --nousb \
        $val \
        --ws --ws.addr 0.0.0.0 --ws.port 32000 --ws.origins "*" \
        --ws.api admin,eth,debug,miner,net,txpool,personal,web3,istanbul \
        --unlock ${ADDRESS} --allow-insecure-unlock --password node/data/keystore/accountPassword \
        --port 30303 \
        &>/dev/null &
done
