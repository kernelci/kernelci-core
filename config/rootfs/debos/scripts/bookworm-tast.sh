#!/bin/bash

# Important: This script is run under QEMU

set -e

export DEBIAN_FRONTEND=noninteractive

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="\
    apt-utils \
    build-essential \
    ca-certificates \
    git \
    dpkg-dev \
    pkg-config \
    libssl-dev \
    libusb-1.0-0-dev \
    wget \
    gettext \
    file \
    quilt \
    autoconf \
    gawk \
    debhelper-compat \
    rdfind \
    symlinks \
    netbase \
    gperf \
    bison \
    libaudit-dev \
    libcap-dev \
    libselinux1-dev \
    binutils-for-host \
    python3:native \
    libgd-dev \
    po-debconf
"

# allow fetching debian sources
echo "deb-src http://deb.debian.org/debian bookworm main" >>/etc/apt/sources.list
apt-get update

apt-get install --no-install-recommends -y  ${BUILD_DEPS}

mkdir -p /tmp/tast
cd /tmp/tast

# the tast test suide is in binary form from ChromeOS and requires a glibc patch for binary
# compatibility, so we rebuild glibc with the CrOS specific patch.
wget https://gitlab.collabora.com/chromiumos-kernelci/chromiumos-overlay/-/raw/kernelci/release-R124-15823.B/sys-libs/glibc/files/local/glibc-2.37/0009-Revert-Add-GLIBC_ABI_DT_RELR-for-DT_RELR-support.patch
apt-get source glibc
cd glibc-*
git apply ../0009-Revert-Add-GLIBC_ABI_DT_RELR-for-DT_RELR-support.patch

# # build and install the patched glibc
DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage --jobs=auto -b -uc && dpkg -i ../*.deb

# allow openssh-server to accept root pubkey auth for tests
apt-get install --no-install-recommends -y openssh-server
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/g' /etc/ssh/sshd_config
systemctl enable ssh

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
cd /tmp
rm -rf /tmp/tast

apt-get remove --purge -y ${BUILD_DEPS}
apt-get autoremove --purge -y
apt-get clean

# re-add some stuff that is removed by accident
apt-get install -y initramfs-tools
