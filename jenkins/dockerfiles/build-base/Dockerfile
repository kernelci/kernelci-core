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
    bc \
    bison \
    bsdmainutils \
    ccache \
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

# Python 2.7
RUN apt-get update && apt-get install --no-install-recommends -y \
    python2.7 \
    python-jinja2 \
    python-keyring \
    python-pyelftools \
    python-requests \
    python-yaml

# Gradually moving everything to Python 3
RUN apt-get update && apt-get install --no-install-recommends -y \
    python3 \
    python3-yaml
