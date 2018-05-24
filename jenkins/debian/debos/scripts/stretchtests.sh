#!/bin/bash

# Important: This script is run under QEMU

set -e

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="libpciaccess-dev \
    libkmod-dev \
    libprocps-dev \
    libcairo2-dev \
    libunwind-dev  \
    libudev-dev  \
    git \
    autoconf \
    xutils-dev \
    autogen \
    libtool \
    automake \
    python \
    python-requests \
    cpio \
    gettext \
    build-essential \
    dpkg-dev \
"

apt-get install --no-install-recommends -y  ${BUILD_DEPS}

########################################################################
# Build tests                                                          #
########################################################################


# Build libdrm
########################################################################

mkdir -p /tmp/tests/libdrm && cd /tmp/tests/libdrm
git clone --depth=1 git://anongit.freedesktop.org/mesa/drm .

autoreconf --force --verbose --install
./configure --enable-intel --prefix=/tmp/tests/igt/usr/
make -j$(nproc) V=1
make -j$(nproc) install V=1

# copy libdrm libraries in the image
cp -a /tmp/tests/igt/usr/lib/lib*.so* /usr/lib/

# Build IGT
########################################################################

mkdir -p /tmp/tests/igt-gpu-tools && cd /tmp/tests/igt-gpu-tools
git clone --depth=1 git://anongit.freedesktop.org/drm/igt-gpu-tools .

PKG_CONFIG_PATH=/tmp/tests/igt/usr/lib/pkgconfig sh autogen.sh
make V=1
mkdir -p /tmp/tests/igt2/usr/bin
cp -a tests/core_auth tests/core_get_client_auth tests/core_getclient tests/core_getstats tests/core_getversion \
    tests/core_prop_blob tests/core_setmaster_vs_auth tests/drm_read tests/kms_addfb_basic tests/kms_atomic \
    tests/kms_flip_event_leak tests/kms_setmode tests/kms_vblank tests/kms_frontbuffer_tracking tests/kms_flip  /tmp/tests/igt2/usr/bin
strip /tmp/tests/igt2/usr/bin/*

# Copy binaries in the image
cp -a /tmp/tests/igt2/usr/bin/* /usr/bin/


# Build v4l2
########################################################################

mkdir -p /tmp/tests/v4l2-compliance && cd /tmp/tests/v4l2-compliance

git clone --depth=1 git://linuxtv.org/v4l-utils.git .

sh bootstrap.sh
./configure --prefix=/tmp/tests/v4l2/usr/ --with-udevdir=/tmp/tests/v4l2/usr/lib/udev
make V=1
make V=1 install
strip /tmp/tests/v4l2/usr/bin/* /tmp/tests/v4l2/usr/lib/*.so* /tmp/tests/v4l2/usr/lib/libv4l/*.so*

# Copy files in the image
rm -rf  /tmp/tests/v4l2/usr/include /tmp/tests/v4l2/usr/share /tmp/tests/v4l2/usr/lib/udev /tmp/tests/v4l2/usr/lib/pkgconfig/
cp -a /tmp/tests/v4l2/usr/* /usr/


########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
cd /tmp
rm -rf /tmp/tests

apt-get remove --purge -y ${BUILD_DEPS}
apt-get remove --purge -y perl-modules-5.24
apt-get autoremove --purge -y
apt-get clean

# re-add some stuff that is removed by accident
apt-get install -y initramfs-tools

