#!/bin/bash

# Important: This script is run under QEMU

set -e

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="\
    autoconf \
    autogen \
    automake \
    autopoint \
    build-essential \
    ca-certificates \
    git \
    gettext \
    libasound2-dev \
    libelf-dev  \
    libglib2.0-dev \
    libjpeg62-turbo-dev \
    libtool \
    libudev-dev  \
"

apt-get install --no-install-recommends -y  ${BUILD_DEPS}

BUILDFILE=/test_suites.json
echo '{  "tests_suites": [' >> $BUILDFILE

# Build v4l2
########################################################################

mkdir -p /tmp/tests/v4l2-compliance && cd /tmp/tests/v4l2-compliance

git clone --depth=1 git://linuxtv.org/v4l-utils.git .

echo '    {"name": "v4l2-compliance", "git_url": "git://linuxtv.org/v4l-utils.git", "git_commit": ' \"`git rev-parse HEAD`\" '}' >> $BUILDFILE

sh bootstrap.sh
./configure --prefix=/tmp/tests/v4l2/usr/ --with-udevdir=/tmp/tests/v4l2/usr/lib/udev

make V=1
make V=1 install
strip /tmp/tests/v4l2/usr/bin/* /tmp/tests/v4l2/usr/lib/*.so* /tmp/tests/v4l2/usr/lib/libv4l/*.so*

# Copy files in the image
rm -rf  /tmp/tests/v4l2/usr/include /tmp/tests/v4l2/usr/share /tmp/tests/v4l2/usr/lib/udev /tmp/tests/v4l2/usr/lib/pkgconfig/
cp -a /tmp/tests/v4l2/usr/* /usr/

echo '  ]}' >> $BUILDFILE

# Build v4l2-get-device
########################################################################

echo "Building v4l2-get-device"

dir="/tmp/tests/v4l2-get-device"
url="https://gitlab.collabora.com/gtucker/v4l2-get-device.git"

mkdir -p "$dir" && cd "$dir"
git clone --depth=1 "$url" .
make
strip v4l2-get-device
make install

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
cd /tmp
rm -rf /tmp/tests

apt-get remove --purge -y ${BUILD_DEPS}
apt-get remove --purge -y perl-modules-5.28
apt-get autoremove --purge -y
apt-get clean

# re-add some stuff that is removed by accident
apt-get install -y initramfs-tools
