#!/bin/bash

# Important: This script is run under QEMU

set -e

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="\
    git \
    python3-setuptools \
    python3-pip \
"

apt-get install --no-install-recommends -y ${BUILD_DEPS}

########################################################################
# Build and install tests                                              #
########################################################################

pip3 install git+https://gitlab.collabora.com/chromiumos/crostests.git

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################

rm -fr /src/crosstests
apt-get remove --purge -y ${BUILD_DEPS} perl-modules-5.28
apt-get autoremove --purge -y
apt-get clean

