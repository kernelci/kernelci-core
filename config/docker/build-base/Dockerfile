FROM debian:bullseye
MAINTAINER "KernelCI TSC" <kernelci-tsc@groups.io>

ARG DEBIAN_FRONTEND=noninteractive

# Docker for jenkins really needs procps otherwise the jenkins side fails
RUN apt-get update && apt-get install --no-install-recommends -y procps

# SSL / HTTPS support
RUN apt-get update && apt-get install --no-install-recommends -y \
    apt-transport-https \
    ca-certificates \
    wget

# Add custom build tools repository
RUN echo 'deb https://repositories.collabora.com/kernelci/ bullseye tools' \
   >> /etc/apt/sources.list.d/tools.list
RUN wget https://repositories.collabora.com/kernelci/pool/tools/c/collabora-archive-keyring/collabora-archive-keyring_0.3+debian11.3_all.deb && \
    dpkg -i collabora-archive-keyring_0.3+debian11.3_all.deb

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
    python3.9 \
    python3-jinja2 \
    python3-keyring \
    python3-pyelftools \
    python3-requests \
    python3-yaml
