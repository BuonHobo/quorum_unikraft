FROM golang:1.21.4-alpine3.18 AS build

COPY quorum_patch.patch /quorum/quorum.patch

WORKDIR /quorum

# Dependencies
RUN set -xe; \
    apk --no-cache add \
    gcc \
    linux-headers \
    musl-dev \
    tzdata \
    wget \
    curl \
    ca-certificates \
    openssl \
    git \
    ; \
    update-ca-certificates;

ARG QUORUM_VERSION=24.4.1

RUN set -xe; \
    wget -O /quorum.tar.gz https://github.com/Consensys/quorum/archive/refs/tags/v${QUORUM_VERSION}.tar.gz; \
    tar -xzf /quorum.tar.gz --strip-components 1 -C /quorum; \
    git apply /quorum/quorum.patch

RUN set -xe; \
    CGO_ENABLED=1 \
    go build -v \
    -buildmode=pie \
    -ldflags "-linkmode external -extldflags '-static-pie'" \
    -tags netgo \
    -o /geth \
    ./cmd/geth

FROM scratch

COPY --from=build /usr/share/zoneinfo/Etc/UTC /usr/share/zoneinfo/Etc/UTC
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt

COPY --from=build /geth /geth
