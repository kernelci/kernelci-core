#!/bin/bash

# Important: This script is run under QEMU

set -e

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="\
    ca-certificates \
    curl \
    libssl-dev \
"

apt-get install --no-install-recommends -y  ${BUILD_DEPS}

mkdir /usr/share/alsa
curl -L -o /tmp/alsa-ucm-conf.tar.gz https://github.com/alsa-project/alsa-ucm-conf/archive/refs/heads/master.tar.gz
tar xvzf /tmp/alsa-ucm-conf.tar.gz -C /usr/share/alsa --strip-components=1 --wildcards "*/ucm" "*/ucm2"

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
