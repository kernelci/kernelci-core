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
BLKTEST_URL=https://github.com/linux-blktests/blktests.git
BLKTESTS_SHA=a0519619
mkdir -p /var/tests/blktest && cd /var/tests/blktest

git clone $BLKTEST_URL .
git checkout $BLKTESTS_SHA

######################################################################
# Apply patch: See https://github.com/linux-blktests/blktests/pull/160
# Author: Denys Fedoryshchenko <denys.f@collabora.com>
# Fix: Update YNL CLI path after kernel commit ab88c2b3739a
# Remove this after the PR is merged upstream
######################################################################
echo -e "\
diff --git a/tests/nvme/056 b/tests/nvme/056
index 2babe69..bdf0d67 100755
--- a/tests/nvme/056
+++ b/tests/nvme/056
@@ -38,15 +38,15 @@ requires() {
 
 have_netlink_cli() {
 	local cli
-	cli=\"\${KERNELSRC}/tools/net/ynl/cli.py\"
+	cli=\"\${KERNELSRC}/tools/net/ynl/pyynl/cli.py\"
 
 	if ! [ -f \"\$cli\" ]; then
-		SKIP_REASONS+=(\"Kernel sources do not have tools/net/ynl/cli.py\")
+		SKIP_REASONS+=(\"Kernel sources do not have tools/net/ynl/pyynl/cli.py\")
 		return 1
 	fi
 
 	if ! \"\$cli\" -h &> /dev/null; then
-		SKIP_REASONS+=(\"Cannot run the kernel tools/net/ynl/cli.py\")
+		SKIP_REASONS+=(\"Cannot run the kernel tools/net/ynl/pyynl/cli.py\")
 		return 1;
 	fi
 
@@ -69,7 +69,7 @@ set_conditions() {
 }
 
 netlink_cli() {
-	\"\${KERNELSRC}/tools/net/ynl/cli.py\" \\
+	\"\${KERNELSRC}/tools/net/ynl/pyynl/cli.py\" \\
 		--spec \"\${KERNELSRC}/Documentation/netlink/specs/ulp_ddp.yaml\" \\
 		\"\$@\"
 }" | patch -p1

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

# Packages to run blktests
apt-get install --no-install-recommends -y blktrace fio gawk pciutils xfsprogs

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
rm -rf /var/tests

apt-get remove --purge -y ${BUILD_DEPS}
apt-get autoremove --purge -y
apt-get clean
