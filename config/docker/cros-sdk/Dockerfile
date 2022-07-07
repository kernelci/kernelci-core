# syntax=docker/dockerfile:1
FROM debian:bullseye-slim
MAINTAINER "KernelCI TSC" <kernelci-tsc@groups.io>

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        netbase \
        python3 \
        sudo \
        ssh \
        wget

RUN apt-get clean \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -u 996 -ms /bin/sh cros
RUN adduser cros sudo && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
RUN mkdir -p /home/cros/chromiumos
RUN chown -R cros /home/cros/chromiumos

# Extra packages needed by kernelCI
RUN apt-get update && apt-get install --no-install-recommends -y \
    python3.9 \
    python3-requests \
    python3-yaml

USER cros
ENV HOME=/home/cros

WORKDIR /kernelci-core
