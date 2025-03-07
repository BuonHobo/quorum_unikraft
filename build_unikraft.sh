#!/bin/bash

podman run --rm --replace -d --name buildkitd --privileged moby/buildkit:latest
kraft build -K _Kraftfile --buildkit-host podman-container://buildkitd --plat qemu -t buonhobo/geth:latest
podman stop buildkitd
