#!/bin/bash
set -x

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
# Build tests                                                          #
########################################################################

BUILDFILE=/test_suites.json
echo '{  "tests_suites": [' >> $BUILDFILE

########################################################################
# Build and install tests                                              #
########################################################################

CROS_URL="https://git.kernel.org/pub/scm/linux/kernel/git/chrome-platform/cros-ec-tests.git"
CROS_SHA=$(git ls-remote ${CROS_URL} | head -n 1 | cut -f 1)

pip3 install git+${CROS_URL}@${CROS_SHA}

echo '    {"name": "cros-ec-tests", "git_url": "'$CROS_URL'", "git_commit": "'$CROS_SHA'" }' >> $BUILDFILE
echo '  ]}' >> $BUILDFILE

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################

rm -fr /src/cros-ec-tests
apt-get remove --purge -y ${BUILD_DEPS} perl-modules-5.28
apt-get autoremove --purge -y
apt-get clean

