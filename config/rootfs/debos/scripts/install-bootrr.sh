#!/bin/sh

BOOTRR_SITE=https://github.com/kernelci/bootrr.git
BOOTRR_VERSION=3ae9fd5dffc667fa96012892ea08532bc6877276

BUILD_DEPS="\
    build-essential \
    ca-certificates \
    git \
"
apt-get install --no-install-recommends -y  ${BUILD_DEPS}

DEST=/opt/bootrr
mkdir -p $DEST

cd /tmp
git clone $BOOTRR_SITE
cd bootrr
git checkout -f $BOOTRR_VERSION
DESTDIR=$DEST make install

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
rm -rf /tmp/bootrr

apt-get remove --purge -y ${BUILD_DEPS}
apt-get autoremove --purge -y
apt-get clean

# re-add some stuff that is removed by accident
apt-get install -y initramfs-tools
