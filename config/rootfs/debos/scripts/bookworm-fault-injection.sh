#!/bin/bash
set -ex

PACKAGES_INSTALL="\
      ca-certificates \
      wget \
"

apt-get install --no-install-recommends -y ${PACKAGES_INSTALL}

# Fetch and install failcmd
wget https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/plain/tools/testing/fault-injection/failcmd.sh -O /usr/local/bin/failcmd
chmod +x /usr/local/bin/failcmd

# Basic validation
if [ ! -x /usr/local/bin/failcmd ]; then
    echo "failcmd installation failed" >&2
    exit 1
fi

apt-get remove --purge -y ${PACKAGES_INSTALL}
apt-get autoremove --purge -y
apt-get clean
