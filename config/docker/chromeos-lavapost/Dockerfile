FROM debian:bullseye-slim
MAINTAINER "KernelCI TSC" <kernelci-tsc@groups.io>

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
          libguestfs-tools \
          linux-image-generic \
          qemu-utils 

ENV LIBGUESTFS_BACKEND=direct \
    HOME=/root

ADD add_modules.sh /add_modules.sh
