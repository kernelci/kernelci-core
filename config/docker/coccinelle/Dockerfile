ARG PREFIX=kernelci/
FROM ${PREFIX}build-base

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install --no-install-recommends -y coccinelle
