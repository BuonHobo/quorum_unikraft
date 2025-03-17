#!/bin/bash

cd deployment

for dir in n*; do
    i="${dir//n}"
    ADDRESS=$(grep -o '"address": *"[^"]*"' n$i/data/keystore/accountKeystore | grep -o '"[^"]*"$' | sed 's/"//g')

    val=""
    if grep -q "validator" n$i/role; then
        val="--istanbul.blockperiod 1 --mine --miner.threads 1 --miner.gasprice 0 --emitcheckpoints"
    fi

    sudo KRAFTKIT_NO_WARN_SUDO=1 kraft run \
            --rm --detach --name n$i \
            -e PRIVATE_CONFIG=ignore \
            --network deployment:192.168.2.$i \
            -v n$i:/node -M 1Gi \
        buonhobo/geth -- /geth \
            --datadir /node/data \
            --networkid 1234 --nodiscover --verbosity 3 \
            --syncmode full --nousb \
            $val \
            --ws --ws.addr 0.0.0.0 --ws.port 32000 --ws.origins "*" \
            --ws.api admin,eth,debug,miner,net,txpool,personal,web3,istanbul \
            --unlock ${ADDRESS} --allow-insecure-unlock --password /node/data/keystore/accountPassword \
            --port 30303
done
