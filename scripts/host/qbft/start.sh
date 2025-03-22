#!/bin/bash

cd deployment

for dir in n*; do
    i="${dir//n}"
    ADDRESS=$(grep -o '"address": *"[^"]*"' n$i/data/keystore/accountKeystore | grep -o '"[^"]*"$' | sed 's/"//g')

    val=""
    if grep -q "validator" n$i/role; then
        val="--istanbul.blockperiod 1 --mine --miner.threads 1 --miner.gasprice 0 --emitcheckpoints"
    fi

    PRIVATE_CONFIG=ignore geth \
        --datadir n$i/data \
        --networkid 1234 --nodiscover --verbosity 0 \
        --syncmode full --nousb \
        $val \
        --ws --ws.addr 0.0.0.0 --ws.port 3200$i --ws.origins "*" \
        --ws.api admin,eth,debug,miner,net,txpool,personal,web3,istanbul \
        --unlock ${ADDRESS} --allow-insecure-unlock --password n$i/data/keystore/accountPassword \
        --port 3030$i \
        &>/dev/null &
done
