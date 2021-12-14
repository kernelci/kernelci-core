#!/bin/bash

# Important: This script is run under QEMU

set -e

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="\
    gcc \
    git \
    make \
    pkgconf \
    autoconf \
    automake \
    bison \
    flex \
    m4 \
    libc6-dev \
    libnuma-dev \
"

apt-get install --no-install-recommends -y  ${BUILD_DEPS}

BUILD_DIR="/ltp"
BUILDFILE=/test_suites.json
echo '{  "tests_suites": [' >> $BUILDFILE

########################################################################
# Build and install tests                                              #
########################################################################
mkdir -p ${BUILD_DIR} && cd ${BUILD_DIR}

git config --global http.sslverify false

LTP_URL="https://github.com/linux-test-project/ltp.git"
LTP_SHA=$(git ls-remote ${LTP_URL} | head -n 1 | cut -f 1)

echo '    {"name": "ltp-tests", "git_url": "'$LTP_URL'", "git_commit": "'$LTP_SHA'" }' >> $BUILDFILE
echo '  ]}' >> $BUILDFILE

git clone --depth=1 -b master ${LTP_URL}
cd ltp && make autotools
./configure
make all
find . -executable -type f -exec strip {} \;
make install

cd testcases/open_posix_testsuite/ && make generate-makefiles prefix=/opt/ltp
make all
make install prefix=/opt/ltp

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################

rm -rf ${BUILD_DIR}
apt-get autoremove --purge -y ${BUILD_DEPS}
apt-get clean
