#!/bin/bash

cd build/unikraft
rm -rf .unikraft .config*

podman run --rm --replace -d -p 8080:1234 --name buildkitd --privileged moby/buildkit:latest --addr tcp://0.0.0.0:1234

toolbox run --container ubuntu-toolbox-24.10 \
    kraft build --no-check-updates --buildkit-host tcp://localhost:8080 --plat qemu --log-level trace --log-type basic
kraft pkg --as oci --name buonhobo/geth .

podman stop buildkitd
