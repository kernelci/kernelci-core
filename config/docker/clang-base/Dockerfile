ARG PREFIX=kernelci/
FROM ${PREFIX}build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    software-properties-common \
    gnupg2

RUN apt-get update && apt-get install --no-install-recommends -y \
    binutils-aarch64-linux-gnu \
    binutils-arm-linux-gnueabihf \
    binutils-riscv64-linux-gnu \
    binutils

# kselftest x86
RUN apt-get update && apt-get install --no-install-recommends -y \
   libc6-dev \
   libcap-dev \
   libcap-ng-dev \
   libelf-dev \
   libpopt-dev \
   libasound2-dev \
   pkg-config

# kselftest arm64
RUN dpkg --add-architecture arm64
RUN apt-get update && apt-get install --no-install-recommends -y \
   libc6-dev:arm64 \
   libcap-dev:arm64 \
   libcap-ng-dev:arm64 \
   libelf-dev:arm64 \
   libpopt-dev:arm64 \
   libasound2-dev:arm64 \
   pkg-config:arm64

# kselftest arm
RUN dpkg --add-architecture armhf
RUN apt-get update && apt-get install --no-install-recommends -y \
   libc6-dev:armhf \
   libcap-dev:armhf \
   libcap-ng-dev:armhf \
   libelf-dev:armhf \
   libpopt-dev:armhf \
   libasound2-dev:armhf \
   pkg-config:armhf

RUN apt-get autoremove -y gcc
