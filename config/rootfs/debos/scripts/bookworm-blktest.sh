#!/bin/bash

# Important: This script is run under QEMU

set -e

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="\
    gcc \
    g++ \
    make \
    git \
    ca-certificates \
    libclang-dev \
    curl \
    python3-pip
"

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install --no-install-recommends -y ${BUILD_DEPS}

# Configure git
git config --global user.email "bot@kernelci.org"
git config --global user.name "KernelCI Bot"

curl https://sh.rustup.rs -sSf | sh -s -- -y
. "$HOME/.cargo/env" || true
# Install dependencies for blktests
cargo install --version=^0.1 rublk
# cleanup cargo cache
rm -rf /root/.cargo/registry
rustup self uninstall -y

########################################################################
# Build blktest                                                        #
########################################################################
# Change nuclearcat/blktests to kernelci/blktests to use the official
# repo as soon as the fix-ynl-location branch is merged.
BLKTEST_URL=https://github.com/nuclearcat/blktests.git
mkdir -p /var/tests/blktest && cd /var/tests/blktest

git clone $BLKTEST_URL .
git checkout fix-ynl-location

make
make install
# contrib required too
mkdir -p /usr/local/blktests/contrib
cp -r contrib/* /usr/local/blktests/contrib

git clone https://github.com/open-iscsi/configshell-fb
cd configshell-fb
pip install . --break-system-packages

git clone https://github.com/nuclearcat/nvmetcli
cd nvmetcli
git checkout rest-install
python3 setup.py install

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
rm -rf /var/tests

apt-get remove --purge -y ${BUILD_DEPS}
apt-get autoremove --purge -y
apt-get clean
