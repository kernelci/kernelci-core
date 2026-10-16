#!/bin/bash

# Important: This script is run under QEMU

set -e

# Tests for NVIDIA Tegra SoCs:
#  - uapi-test: the host1x/TegraDRM userspace interface (syncpoints, channels,
#    job submission, VIC/NVDEC engines); a single binary, /usr/bin/uapi-test.
#  - tegra-tests: board sanity tests (expected devices and drivers, kernel log,
#    CPU hotplug and frequency scaling, DRM devices); Python, in
#    /opt/tegra-tests.
UAPI_TEST_URL=https://github.com/cyndis/uapi-test.git
UAPI_TEST_SHA=ad8a69e2641bb0c2a399b9c03d65f68e74220094
TEGRA_TESTS_URL=https://github.com/thierryreding/tegra-tests.git
TEGRA_TESTS_SHA=73781c4940a3b568d174ff2240364e12d9c32238

BUILD_DEPS="\
      ca-certificates \
      cargo \
      git \
      rustc \
"

apt-get update
apt-get install --no-install-recommends -y ${BUILD_DEPS}

mkdir /tmp/uapi-test
cd /tmp/uapi-test
git clone ${UAPI_TEST_URL} .
git reset --hard ${UAPI_TEST_SHA}
CARGO_HOME=/tmp/cargo CARGO_PROFILE_RELEASE_DEBUG=0 CARGO_PROFILE_RELEASE_STRIP=true \
    cargo build --release --locked
install -m 755 target/release/uapi-test /usr/bin/uapi-test
echo ${UAPI_TEST_SHA} > /etc/uapi-test.version

git clone ${TEGRA_TESTS_URL} /opt/tegra-tests
git -C /opt/tegra-tests reset --hard ${TEGRA_TESTS_SHA}
rm -rf /opt/tegra-tests/.git
echo ${TEGRA_TESTS_SHA} > /etc/tegra-tests.version

cd /tmp
rm -rf /tmp/uapi-test /tmp/cargo

# Cleanup: remove files and packages we don't want in the images
apt-get remove --purge -y ${BUILD_DEPS}
apt-get autoremove --purge -y
apt-get clean
