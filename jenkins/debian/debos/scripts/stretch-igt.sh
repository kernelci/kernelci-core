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
    libssl-dev \
    libdw-dev \
    liblzma-dev \
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

BUILDFILE=/test_suites.json
echo '{  "tests_suites": [' >> $BUILDFILE

# Build libdrm
########################################################################

mkdir -p /tmp/tests/libdrm && cd /tmp/tests/libdrm
git clone --depth=1 git://anongit.freedesktop.org/mesa/drm .

echo '    {"name": "drm", "git_url": "git://anongit.freedesktop.org/mesa/drm", "git_commit": ' \"`git rev-parse HEAD`\" '},' >> $BUILDFILE

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

echo '    {"name": "igt-gpu-tools", "git_url": "git://anongit.freedesktop.org/drm/igt-gpu-tools", "git_commit": ' \"`git rev-parse HEAD`\" '}' >> $BUILDFILE


PKG_CONFIG_PATH=/tmp/tests/igt/usr/lib/pkgconfig sh autogen.sh
make V=1
mkdir -p /tmp/tests/igt2/usr/bin
cp -a \
   tests/core_auth \
   tests/core_getclient \
   tests/core_getstats \
   tests/core_getversion \
   tests/core_prop_blob \
   tests/core_setmaster_vs_auth \
   tests/drm_read \
   tests/kms_addfb_basic \
   tests/kms_atomic \
   tests/kms_flip_event_leak \
   tests/kms_setmode \
   tests/kms_vblank \
   tests/kms_frontbuffer_tracking \
   tests/kms_flip  \
   tests/kms_cursor_legacy \
   tests/testdisplay \
   /tmp/tests/igt2/usr/bin
strip /tmp/tests/igt2/usr/bin/*

# Copy binaries in the image
cp -a /tmp/tests/igt2/usr/bin/* /usr/bin/


echo '  ]}' >> $BUILDFILE

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
