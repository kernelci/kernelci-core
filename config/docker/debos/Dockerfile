FROM debian:bullseye-slim

ARG DEBIAN_FRONTEND=noninteractive

# Docker for Jenkins really needs procps otherwise the Jenkins side fails
RUN apt-get update && apt-get install --no-install-recommends -y procps

# Set HOME to a writable directory in case something wants to cache things
# (e.g. obs)
ENV HOME=/tmp
ENV GOPATH=/usr/local/go
ENV PATH=$PATH:/usr/local/go/bin

# SSL / HTTPS support
RUN apt-get update && apt-get install --no-install-recommends -y \
    apt-transport-https \
    ca-certificates

# Dependencies to build debos
RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc \
    golang-go \
    git \
    libc6-dev \
    libostree-dev

# Build debos
RUN go get github.com/go-debos/debos/cmd/debos && \
    go install github.com/go-debos/debos/cmd/debos

# Dependencies to run debos
RUN apt-get update && apt-get install --no-install-recommends -y \
    binfmt-support \
    busybox \
    debian-ports-archive-keyring \
    debootstrap \
    dosfstools \
    e2fsprogs \
    linux-image-amd64 \
    parted \
    pkg-config \
    qemu-system-x86 \
    qemu-user-static \
    systemd-container

# Extra packages needed by kernelCI
RUN apt-get update && apt-get install --no-install-recommends -y \
    python3.9 \
    python3-requests \
    python3-yaml \
    ssh \
    xz-utils

# Jenkins hacks
RUN useradd -u 996 -ms /bin/sh jenkins
