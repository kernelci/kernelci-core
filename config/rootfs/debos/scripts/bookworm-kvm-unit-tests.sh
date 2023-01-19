#!/bin/bash

# Important: This script is run under QEMU

set -e

RELEASE=3c1736b1344b9831f17fbd64f95ea89c279564c6

BUILD_DEPS="\
      gcc \
      git \
      ca-certificates \
      libc6-dev \
      make \
"

apt-get install --no-install-recommends -y ${BUILD_DEPS}

# test-definitions is going to go looking for /opt/kvm-unit-tests
# so build there
mkdir -p /opt
cd /opt
git clone https://gitlab.com/kvm-unit-tests/kvm-unit-tests
cd /opt/kvm-unit-tests
git reset --hard ${RELEASE}
./configure
make

# Cleanup: remove files and packages we don't want in the images
apt-get remove --purge -y ${BUILD_DEPS}
apt-get remove --purge -y libgtest-dev
apt-get autoremove --purge -y
apt-get clean
