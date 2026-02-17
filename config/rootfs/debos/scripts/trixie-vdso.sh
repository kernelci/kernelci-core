#!/bin/bash

# Important: This script is run under QEMU

set -e

RELEASE=d6d600a1b2d82ea59111e060214bd3433524509d

BUILD_DEPS="\
      autoconf \
      automake \
      ca-certificates \
      gcc \
      git \
      libc6-dev \
      libtool \
      make \
"

apt-get install --no-install-recommends -y ${BUILD_DEPS}

# test-definitions is going to go looking for /usr/lib*/libhugetlbfs
# so build there
mkdir /tmp/vdso
cd /tmp/vdso
git clone https://github.com/nathanlynch/vdsotest
cd vdsotest
git reset --hard ${RELEASE}
autoreconf --install --symlink
./configure --prefix=/opt/vdso
make
make install
cd /tmp
rm -r ./vdso

# Cleanup: remove files and packages we don't want in the images 
apt-get remove --purge -y ${BUILD_DEPS}
apt-get remove --purge -y libgtest-dev
apt-get autoremove --purge -y
apt-get clean
