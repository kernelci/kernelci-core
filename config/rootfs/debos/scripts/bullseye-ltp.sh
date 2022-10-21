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

git clone -b master ${LTP_URL}
cd ltp

# See https://github.com/kernelci/kernelci-core/issues/948
echo -e "\
diff --git a/testcases/open_posix_testsuite/bin/run-posix-option-group-test.sh b/testcases/open_posix_testsuite/bin/run-posix-option-group-test.sh
index 1bbdddfd5..de84b9e6f 100755
--- a/testcases/open_posix_testsuite/bin/run-posix-option-group-test.sh
+++ b/testcases/open_posix_testsuite/bin/run-posix-option-group-test.sh
@@ -25,7 +25,7 @@ run_option_group_tests()
 {
\tlocal list_of_tests

-\tlist_of_tests=\`find \$1 -name '*.run-test' | sort\`
+\tlist_of_tests=\`find \$1 -name run.sh | sort\`

\tif [ -z \"\$list_of_tests\" ]; then
\t\techo \".run-test files not found under \$1, have been the tests compiled?\"
" | patch -p1

make autotools
./configure
make all
find . -executable -type f -exec strip {} \;
make install

cd testcases/open_posix_testsuite/ && ./configure
make all
make install prefix=/opt/ltp

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################

rm -rf ${BUILD_DIR}
apt-get autoremove --purge -y ${BUILD_DEPS}
apt-get clean
