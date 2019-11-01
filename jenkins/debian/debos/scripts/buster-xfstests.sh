#!/bin/bash

#####################################################
# This script create buster image for xfstests
#####################################################

set -e

# Install required xfstests packages
apt-get install --no-install-recommends xfslibs-dev uuid-dev libtool-bin \
	        e2fsprogs automake gcc libuuid1 quota attr libattr1-dev make \
	        libacl1-dev libaio-dev xfsprogs libgdbm-dev gawk fio dbench \
	        uuid-runtime python sqlite3 git bc bsdmainutils acl -y

apt-get install perl hostname net-tools -y

# Clone repo
git clone git://git.kernel.org/pub/scm/fs/xfs/xfstests-dev.git /xfstests

# Setup xfstests accounts, directory
useradd fsgqa -m
useradd 123456-fsgqa

mkdir /test /scratch

# Setup default xfstests config 
cat > /xfstests/local.config <<'EOF'
export TEST_DEV=/dev/sda2
export TEST_DIR=/test
export SCRATCH_DEV=/dev/sda3
export SCRATCH_MNT=/scratch
#export SCRATCH_DEV_POOL="/dev/xvdc /dev/xvdd /dev/xvde /dev/xvdf /dev/xvdg"
EOF

# Build xfstests 
cd /xfstests && make && make install
