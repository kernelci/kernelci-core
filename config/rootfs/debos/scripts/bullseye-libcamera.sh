#!/bin/bash

# Important: This script is run under QEMU

set -e

# No libudev, it's needed only for hotplug detection
# No libboost or raspberrypi pipeline, should be added if tested on raspberrypi

BUILD_DEPS="\
      g++ \
      ninja-build \
      cmake \
      python3-yaml \
      python3-ply \
      python3-jinja2 \
      python3-setuptools \
      libgnutls28-dev \
      openssl \
      pkg-config \
      libevent-dev \
      python3-pip \
      git \
      ca-certificates \
"

# Get latest libgtest from backports
echo 'deb http://deb.debian.org/debian bullseye-backports main' >> /etc/apt/sources.list
apt-get update
apt-get install --no-install-recommends -y libgtest-dev

apt-get install --no-install-recommends -y  ${BUILD_DEPS}

# Get latest meson from pip
pip3 install meson

BUILDFILE=/test_suites.json
echo '{  "tests_suites": [' >> $BUILDFILE

# Build libcamera and lc-compliance
########################################################################

LIBCAMERA_URL=https://git.linuxtv.org/libcamera.git
mkdir -p /var/tests/libcamera && cd /var/tests/libcamera

git clone --depth=1 $LIBCAMERA_URL .

echo '    {"name": "lc-compliance", "git_url": "'$LIBCAMERA_URL'", "git_commit": ' \"`git rev-parse HEAD`\" '}' >> $BUILDFILE

meson build --prefix=/usr -Ddocumentation=disabled -Dgstreamer=disabled -Dpipelines=uvcvideo,rkisp1
ninja -C build install

echo '  ]}' >> $BUILDFILE

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
rm -rf /var/tests

apt-get remove --purge -y ${BUILD_DEPS}
apt-get remove --purge -y libgtest-dev
apt-get autoremove --purge -y
apt-get clean

# re-add some stuff that is removed by accident
apt-get install -y initramfs-tools
