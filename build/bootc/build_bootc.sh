#!/bin/bash

# Ensure the image is fetched
sudo podman build ./build/bootc -t buonhobo/quorum-bootc:latest --net host
sudo podman run \
    --rm \
    -it \
    --privileged \
    --pull=newer \
    --security-opt label=type:unconfined_t \
    -v ./build/bootc/config.json:/config.json:ro \
    -v ./build/bootc:/output \
    -v /var/lib/containers/storage:/var/lib/containers/storage \
    quay.io/centos-bootc/bootc-image-builder:latest \
    --type qcow2 \
    --rootfs xfs \
	--use-librepo=True \
    localhost/buonhobo/quorum-bootc:latest