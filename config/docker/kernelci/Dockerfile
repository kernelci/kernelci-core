# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2021, 2022 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

FROM python:3.10
MAINTAINER "KernelCI TSC" <kernelci-tsc@groups.io>

# Upgrade pip3 - never mind the warning about running this as root
RUN pip3 install --upgrade pip

ARG core_rev=main
RUN git clone \
    --depth=1 \
    https://github.com/kernelci/kernelci-core.git \
    /tmp/kernelci-core
WORKDIR /tmp/kernelci-core
RUN git fetch origin $core_rev
RUN git checkout FETCH_HEAD
RUN pip3 install -r requirements-dev.txt
RUN python3 setup.py install
RUN cp -R config /etc/kernelci/
WORKDIR /root
RUN rm -rf /tmp/kernelci-core

RUN useradd kernelci -u 1000 -d /home/kernelci -s /bin/bash
RUN mkdir -p /home/kernelci
RUN chown kernelci: /home/kernelci
USER kernelci
ENV PATH=$PATH:/home/kernelci/.local/bin
WORKDIR /home/kernelci
