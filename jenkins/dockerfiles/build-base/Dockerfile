FROM debian:buster
MAINTAINER "Matt Hart" <matt@mattface.org>

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
    tar \
    u-boot-tools \
    wget \
    xz-utils

# Python 3.7
RUN apt-get update && apt-get install --no-install-recommends -y \
    python3.7 \
    python3-jinja2 \
    python3-keyring \
    python3-pip \
    python3-pyelftools \
    python3-requests \
    python3-yaml

# kernelci-core tools and dependencies
RUN git clone --depth 1 --branch master https://github.com/kernelci/kernelci-core.git /opt/kernelci-core; \
  (cd /opt/kernelci-core; pip3 install `cat requirements.txt`)
