FROM debian:bullseye-slim
MAINTAINER "KernelCI TSC" <kernelci-tsc@groups.io>

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    wget\
    iputils-ping \
    net-tools \
    ssh

RUN mkdir /keys

ADD id_rsa_chromeos_flash /keys/id_rsa_chromeos_flash
RUN chmod 0600 /keys/id_rsa_chromeos_flash
