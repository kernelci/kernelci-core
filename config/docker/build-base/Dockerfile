FROM debian:bullseye
MAINTAINER "KernelCI TSC" <kernelci-tsc@groups.io>

ARG DEBIAN_FRONTEND=noninteractive

# Prepare environment for building packages
RUN set -ex \
    && sed -i -- 's/# deb-src/deb-src/g' /etc/apt/sources.list \
    && echo "deb-src http://deb.debian.org/debian bullseye main non-free contrib" >>/etc/apt/sources.list \
    && echo "deb-src http://deb.debian.org/debian-security/ bullseye-security main contrib non-free" >>/etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
               build-essential \
               cdbs \
               devscripts \
               equivs \
               fakeroot \
               wget \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

ADD kmod_kci.patch /root/debs/kmod_kci.patch

# Prepare kmod sources, patch, install dependencies, build
RUN cd /root/debs && \
    apt-get source kmod && \
    cd kmod-28 && \
    patch -p1 <../kmod_kci.patch && \
    mk-build-deps -ir -t "apt-get -o Debug::pkgProblemResolver=yes -y --no-install-recommends" && \
    debuild -b -uc -us

FROM debian:bullseye

# Fetch debs from previous stage
COPY --from=0 /root/debs/*.deb /root/
RUN dpkg -i /root/*.deb && rm /root/*.deb

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
    python3.9 \
    python3-jinja2 \
    python3-keyring \
    python3-pyelftools \
    python3-requests \
    python3-yaml
