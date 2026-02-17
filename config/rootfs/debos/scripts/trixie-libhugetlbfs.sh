#!/bin/bash

# Important: This script is run under QEMU

set -e

RELEASE=1322884fb0d55dc55f53563c1aa6328d118997e7

BUILD_DEPS="\
      automake
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
./autogen.sh
./configure
make BUILDTYPE=NATIVEONLY
make BUILDTYPE=NATIVEONLY install

# Cleanup: remove files and packages we don't want in the images 
apt-get remove --purge -y ${BUILD_DEPS}
apt-get remove --purge -y libgtest-dev
apt-get autoremove --purge -y
apt-get clean
