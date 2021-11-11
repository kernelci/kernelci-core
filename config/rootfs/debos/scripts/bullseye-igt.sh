#!/bin/bash

# Important: This script is run under QEMU

set -e

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="\
    bison \
    build-essential \
    ca-certificates \
    cpio \
    dpkg-dev \
    flex \
    gettext \
    git \
    libcairo2-dev \
    libdw-dev \
    libkmod-dev \
    liblzma-dev \
    libpciaccess-dev \
    libprocps-dev \
    libtool \
    libudev-dev  \
    libunwind-dev  \
    libssl-dev \
    meson \
    ninja-build \
    pkg-config \
    python3 \
    python3-requests \
    xutils-dev \
"

apt-get install --no-install-recommends -y  ${BUILD_DEPS}

########################################################################
# Build tests                                                          #
########################################################################

BUILDFILE=/test_suites.json
echo '{  "tests_suites": [' >> $BUILDFILE

# Build libdrm
########################################################################

DRM_URL=git://anongit.freedesktop.org/mesa/drm

mkdir -p /tmp/tests/libdrm && cd /tmp/tests/libdrm
git clone --depth=1 $DRM_URL .

echo '    {"name": "drm", "git_url": "'$DRM_URL'", "git_commit": ' \"`git rev-parse HEAD`\" '},' >> $BUILDFILE

mkdir build
meson -Dprefix=/usr/ build
ninja -C build install


# Build IGT
########################################################################

IGT_URL=https://gitlab.freedesktop.org/drm/igt-gpu-tools.git

mkdir -p /tmp/tests/igt-gpu-tools && cd /tmp/tests/igt-gpu-tools
git clone --depth=1 $IGT_URL .

echo '    {"name": "igt-gpu-tools", "git_url": "'$IGT_URL'", "git_commit": ' \"`git rev-parse HEAD`\" '}' >> $BUILDFILE

mkdir build
meson -Dprefix=/usr/ build
ninja -C build install

rm -rf /usr/libexec/igt-gpu-tools/benchmarks

for f in $(find /usr/libexec/igt-gpu-tools -executable -type f); do
    echo "$f"
    strip "$f"
done

echo '  ]}' >> $BUILDFILE

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
rm -rf /tmp/tests
rm -rf /usr/include

apt-get remove --purge -y ${BUILD_DEPS}
rm -rf /usr/lib/python3/dist-packages/mesonbuild # to remove stale .pyc files
apt-get autoremove --purge -y
apt-get clean

# re-add some stuff that is removed by accident
apt-get install -y initramfs-tools
