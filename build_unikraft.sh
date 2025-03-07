#!/bin/bash

podman run --rm --replace -d --name buildkitd --privileged moby/buildkit:latest
kraft pkg -K _Kraftfile --buildkit-host podman-container://buildkitd --plat qemu --name buonhobo/geth:latest
podman stop buildkitd
