# -----------------------------------------------------------------------------
# Debian Buster version of build-base
#

FROM debian:buster
MAINTAINER "KernelCI TSC" <kernelci-tsc@groups.io>

ARG DEBIAN_FRONTEND=noninteractive

# Docker for jenkins really needs procps otherwise the jenkins side fails
RUN apt-get update && apt-get install --no-install-recommends -y procps

# SSL / HTTPS support
RUN apt-get update && apt-get install --no-install-recommends -y \
    apt-transport-https \
    ca-certificates

# Host build tools
RUN apt-get update && apt-get install --no-install-recommends -y \
    bash \
    bc \
    bison \
    bsdmainutils \
    ccache \
    cpio \
    flex \
    g++ \
    gcc \
    git \
    kmod \
    libssl-dev \
    libelf-dev \
    lzop \
    make \
    rsync \
    tar \
    u-boot-tools \
    wget \
    xz-utils

# Python 3.7
RUN apt-get update && apt-get install --no-install-recommends -y \
    python3.7 \
    python3-jinja2 \
    python3-keyring \
    python3-pyelftools \
    python3-requests \
    python3-yaml

# -----------------------------------------------------------------------------
# LLVM/Clang 10
#

RUN apt-get update && apt-get install --no-install-recommends -y \
    software-properties-common \
    gnupg2

RUN wget -q -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add -
RUN apt-add-repository 'deb http://apt.llvm.org/buster/ llvm-toolchain-buster-10 main'

RUN apt-get update && apt-get install --no-install-recommends -y \
    binutils-aarch64-linux-gnu \
    binutils-arm-linux-gnueabihf \
    binutils-riscv64-linux-gnu \
    binutils \
    clang-10 lld-10 llvm-10

ENV PATH=/usr/lib/llvm-10/bin:${PATH}

# kselftest x86
RUN apt-get update && apt-get install --no-install-recommends -y \
   libc6-dev \
   libcap-dev \
   libcap-ng-dev \
   libelf-dev \
   libpopt-dev

# kselftest arm64
RUN dpkg --add-architecture arm64
RUN apt-get update && apt-get install --no-install-recommends -y \
   libc6-dev:arm64 \
   libcap-dev:arm64 \
   libcap-ng-dev:arm64 \
   libelf-dev:arm64 \
   libpopt-dev:arm64

# kselftest arm
RUN dpkg --add-architecture armhf
RUN apt-get update && apt-get install --no-install-recommends -y \
   libc6-dev:armhf \
   libcap-dev:armhf \
   libcap-ng-dev:armhf \
   libelf-dev:armhf \
   libpopt-dev:armhf

RUN apt-get autoremove -y gcc
