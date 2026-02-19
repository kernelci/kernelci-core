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
    python3 \
"

apt-get install --no-install-recommends -y  ${BUILD_DEPS}

BUILD_DIR="/rt-tests"
BUILDFILE=/test_suites.json
echo '{  "tests_suites": [' >> $BUILDFILE

mkdir -p ${BUILD_DIR} && cd ${BUILD_DIR}
git config --global http.sslverify false

GIT_URL="https://git.kernel.org/pub/scm/utils/rt-tests/rt-tests.git"
# Current rt-tests commit used for deterministic builds (main branch HEAD at snapshot time).
# Update the value below when you intentionally rebuild against a newer rt-tests snapshot.
# To refresh:
#   GIT_SHA=$(git ls-remote ${GIT_URL} refs/heads/main | cut -f 1)
GIT_SHA=4e68b52f0e0c9777c91088948374c6ee3d4a1f6b

echo '    {"name": "rt-tests", "git_url": "'$GIT_URL'", "git_commit": "'$GIT_SHA'" }' >> $BUILDFILE
echo '  ]}' >> $BUILDFILE

git clone --depth=1 -b main ${GIT_URL}
cd rt-tests
make -j$(nproc)
find . -executable -type f -exec strip {} \;
make install

rm -rf ${BUILD_DIR}
apt-get autoremove --purge -y ${BUILD_DEPS}
apt-get clean
