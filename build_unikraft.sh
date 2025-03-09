#!/bin/bash

podman run --rm --replace -d -p 8080:1234 --name buildkitd --privileged moby/buildkit:latest --addr tcp://0.0.0.0:1234
toolbox run kraft build -K Kraftfile --buildkit-host tcp://localhost:8080 --plat qemu --log-level trace --log-type basic
podman stop buildkitd
