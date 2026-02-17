#!/bin/bash

# Important: This script is run under QEMU

set -e

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="\
    build-essential \
    ca-certificates \
    git \
    wget \
    pkg-config \
    libssl-dev \
    libusb-1.0-0-dev
"

apt-get install --no-install-recommends -y  ${BUILD_DEPS}

mkdir -p /tmp/tests
cd /tmp/tests

wget --no-verbose --inet4-only --no-clobber --tries 5 \
    https://chromium.googlesource.com/chromiumos/platform/ec/+archive/refs/heads/gsc_utils.tar.gz

tar -xzf gsc_utils.tar.gz
cd extra/usb_updater
make
cp gsctool /usr/bin

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
cd /tmp
rm -rf /tmp/tests

apt-get remove --purge -y ${BUILD_DEPS}
apt-get autoremove --purge -y
apt-get clean

# re-add some stuff that is removed by accident
apt-get install -y initramfs-tools
