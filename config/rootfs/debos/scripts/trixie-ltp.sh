#!/bin/bash

# Build LTP outside the target chroot so foreign architectures use a
# cross-compiler instead of running a native compiler under QEMU.

set -euo pipefail

TARGET_ARCH=${1:?target architecture is required}

LTP_URL="https://github.com/linux-test-project/ltp.git"
LTP_SHA=20260529

# Version of Kirk to install
KIRK_VERSION=v4.1.0

case "${TARGET_ARCH}" in
    amd64)
        GNU_TRIPLET=x86_64-linux-gnu
        ;;
    arm64)
        GNU_TRIPLET=aarch64-linux-gnu
        ;;
    armhf)
        GNU_TRIPLET=arm-linux-gnueabihf
        ;;
    riscv64)
        GNU_TRIPLET=riscv64-linux-gnu
        ;;
    *)
        echo "Unsupported LTP cross-compilation architecture: ${TARGET_ARCH}" >&2
        exit 1
        ;;
esac

HOST_BUILD_TOOLS=(
    autoconf
    automake
    bison
    flex
    gcc
    git
    m4
    make
    patch
    pkgconf
    "${GNU_TRIPLET}-ar"
    "${GNU_TRIPLET}-gcc"
    "${GNU_TRIPLET}-ranlib"
    "${GNU_TRIPLET}-readelf"
    "${GNU_TRIPLET}-strip"
)
for tool in "${HOST_BUILD_TOOLS[@]}"; do
    command -v "${tool}" >/dev/null || {
        echo "Missing LTP host build tool: ${tool}" >&2
        exit 1
    }
done

BUILD_DIR=$(mktemp -d /tmp/ltp-build.XXXXXX)
BUILDFILE="${ROOTDIR}/test_suites.json"
cat > "${BUILDFILE}" <<EOF
{  "tests_suites": [
    {"name": "ltp-tests", "git_url": "${LTP_URL}", "git_commit": "${LTP_SHA}" }
  ]}
EOF

########################################################################
# Build and install tests                                              #
########################################################################
cd "${BUILD_DIR}"

git config --global http.sslverify false

git clone --depth 1 -b "${LTP_SHA}" "${LTP_URL}"
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

NBCPU=$(nproc)
BUILD_TRIPLET=$(gcc -dumpmachine)
TARGET_CC="${GNU_TRIPLET}-gcc --sysroot=${ROOTDIR}"
TARGET_AR="${GNU_TRIPLET}-ar"
TARGET_RANLIB="${GNU_TRIPLET}-ranlib"
TARGET_STRIP="${GNU_TRIPLET}-strip"
TARGET_READELF="${GNU_TRIPLET}-readelf"

export PKG_CONFIG_SYSROOT_DIR="${ROOTDIR}"
export PKG_CONFIG_LIBDIR="\
${ROOTDIR}/usr/lib/${GNU_TRIPLET}/pkgconfig:\
${ROOTDIR}/usr/share/pkgconfig"

make autotools
./configure \
    --build="${BUILD_TRIPLET}" \
    --host="${GNU_TRIPLET}" \
    --prefix=/opt/ltp \
    CC="${TARGET_CC}" \
    AR="${TARGET_AR}" \
    RANLIB="${TARGET_RANLIB}"
make all -j"${NBCPU}"
make install DESTDIR="${ROOTDIR}"

cd testcases/open_posix_testsuite/
./configure \
    --build="${BUILD_TRIPLET}" \
    --host="${GNU_TRIPLET}" \
    CC="${TARGET_CC}"
make all -j"${NBCPU}" \
    CC="${TARGET_CC}" \
    AR="${TARGET_AR}" \
    RANLIB="${TARGET_RANLIB}"
make install DESTDIR="${ROOTDIR}" prefix=/opt/ltp

# Strip target ELF files without attempting to process installed scripts.
while IFS= read -r -d '' target_file; do
    if "${TARGET_READELF}" -h "${target_file}" >/dev/null 2>&1; then
        "${TARGET_STRIP}" --strip-unneeded "${target_file}"
    fi
done < <(find "${ROOTDIR}/opt/ltp" -type f -print0)

########################################################################
# Install kirk                                                         #
########################################################################

git clone https://github.com/linux-test-project/kirk "${ROOTDIR}/opt/kirk"
cd "${ROOTDIR}/opt/kirk"
git reset --hard "${KIRK_VERSION}"
rm -rf .git

# test-definitions' ltp.sh resolves the runner as a bare "kirk" through
# PATH, so make it reachable without every caller having to know where
# kirk is installed.
ln -sf /opt/kirk/kirk "${ROOTDIR}/usr/bin/kirk"

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################

rm -rf "${BUILD_DIR}"
