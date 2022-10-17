#!/bin/bash

# Important: This script is run under QEMU

set -e

BUILD_DEPS="\
      automake \
      make \
      libtool \
      git \
      openssl \
      ca-certificates \
      curl \
"

apt-get install --no-install-recommends -y  ${BUILD_DEPS}

BUILDFILE=/test_suites.json
echo '{  "tests_suites": [' >> $BUILDFILE

# Build libasound2
########################################################################

LIBASOUND_PREFIX_DIR=/usr/local/
LIBASOUND_URL=https://github.com/alsa-project/alsa-lib.git
mkdir -p /var/tests/libasound2 && cd /var/tests/libasound2

git clone --depth=1 $LIBASOUND_URL .

echo '    {"name": "libasound2", "git_url": "'$LIBASOUND_URL'", "git_commit": ' \"`git rev-parse HEAD`\" '}' >> $BUILDFILE

./gitcompile --prefix=$LIBASOUND_PREFIX_DIR
make install

# Make the libasound we built take precendence over the one from the distro
echo $LIBASOUND_PREFIX_DIR/lib > /etc/ld.so.conf.d/1-libasound.conf

echo '  ]}' >> $BUILDFILE

# Download alsa-ucm-conf
########################################################################

UCM_CONF_DIR=$LIBASOUND_PREFIX_DIR/share/alsa
mkdir -p /var/tests/ucm-conf && cd /var/tests/ucm-conf
mkdir -p $UCM_CONF_DIR
curl -L -o alsa-ucm-conf.tar.gz https://github.com/alsa-project/alsa-ucm-conf/archive/refs/heads/master.tar.gz
tar xvzf alsa-ucm-conf.tar.gz -C $UCM_CONF_DIR --strip-components=1 --wildcards "*/ucm" "*/ucm2"

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
rm -rf /var/tests

apt-get remove --purge -y ${BUILD_DEPS}
apt-get autoremove --purge -y
apt-get clean

# re-add some stuff that is removed by accident
apt-get install -y initramfs-tools
