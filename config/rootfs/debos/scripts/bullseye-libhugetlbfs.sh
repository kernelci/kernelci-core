#!/bin/bash

# Important: This script is run under QEMU

set -e

RELEASE=02df38e93e25e07f4d54edae94fb4ec90b7a2824

BUILD_DEPS="\
      gcc \
      git \
      ca-certificates \
      libc6-dev \
      make \
      wget \
"

apt-get install --no-install-recommends -y ${BUILD_DEPS}

# test-definitions is going to go looking for /usr/lib*/libhugetlbfs
# so build there
mkdir /usr/libhugetlbfs
cd /usr/libhugetlbfs
git clone https://github.com/libhugetlbfs/libhugetlbfs
cd libhugetlbfs
git reset --hard ${RELEASE}
make BUILDTYPE=NATIVEONLY

# Cleanup: remove files and packages we don't want in the images 
apt-get remove --purge -y ${BUILD_DEPS}
apt-get remove --purge -y libgtest-dev
apt-get autoremove --purge -y
apt-get clean
