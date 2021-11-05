#!/bin/sh

set -e
FIRMWARE_SITE=https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git
FIRMWARE_VERSION=d526e044bddaa2c2ad855c7296147e49be0ab03c

DEST=${ROOTDIR}/lib/firmware
mkdir -p $DEST

# Because the linux-firmware repo is very big, we use the following
# git init hack to fetch a single shallow commit to minimize time,
# space and network bandwidth
TMP_REPO=/tmp/linux-firmware
mkdir -p $TMP_REPO && cd $TMP_REPO
git init
git remote add origin $FIRMWARE_SITE
git fetch --depth 1 origin $FIRMWARE_VERSION
git checkout FETCH_HEAD

for fw_file in "$@"
do
    cp --parents "$fw_file" $DEST
done

########################################################################
# Cleanup: remove downloaded firmware files
########################################################################
rm -rf $TMP_REPO
