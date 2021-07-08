FROM debian:buster-slim

ARG DEBIAN_FRONTEND=noninteractive

# Docker for Jenkins really needs procps otherwise the Jenkins side fails
RUN apt-get update && apt-get install --no-install-recommends -y procps

ENV FORCE_UNSAFE_CONFIGURE=1

# SSL / HTTPS support
RUN apt-get update && apt-get install --no-install-recommends -y \
    apt-transport-https \
    ca-certificates

# Dependencies to run buildroot
RUN apt-get update && apt-get install --no-install-recommends -y \
    bc \
    bzip2 \
    cpio \
    file \
    gcc \
    g++ \
    git \
    make \
    rsync \
    patch \
    python3 \
    unzip \
    wget \
    xz-utils

