FROM debian:stretch
MAINTAINER "Matt Hart" <matt@mattface.org>

ARG DEBIAN_FRONTEND=noninteractive

# SSL / HTTPS support
RUN apt-get update && apt-get install --no-install-recommends -y \
    apt-transport-https \
    ca-certificates

RUN apt-get update && apt-get install --no-install-recommends -y \
    bc \
    bison \
    bsdmainutils \
    bzip2 \
    ccache \
    flex \
    git \
    kmod \
    libssl-dev \
    libelf-dev \
    lzop \
    make \
    tar \
    wget

RUN wget \
    -O /usr/gcc-6.3.0-mips-linux.tar.bz2 \
    https://storage.kernelci.org/images/toolchain/gcc-6.3.0-mips-linux.tar.bz2
RUN tar -C /usr -a --strip-components=1 -jxvf /usr/gcc-6.3.0-mips-linux.tar.bz2
RUN rm /usr/gcc-6.3.0-mips-linux.tar.bz2

RUN apt-get update && apt-get install --no-install-recommends -y \
    libisl15 \
    libmpfr4
