#!/bin/bash

# Important: This script is run under QEMU

set -e

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="libglib2.0-dev \
    git \
    autoconf \
    autogen \
    libtool \
    automake \
    gettext \
    build-essential \
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
