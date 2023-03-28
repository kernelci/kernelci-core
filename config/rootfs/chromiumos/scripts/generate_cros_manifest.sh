#!/bin/bash
set -e
BRANCH=$1
DATA_DIR=$(pwd)
USERNAME=$(/usr/bin/id -run)

function cleanup()
{
  rc=$?
  # During development we might need to keep SDK for debugging
  # then please "touch .keep" in --output directory
  if [ -f "$DATA_DIR/../.keep" ]; then
    echo "Keeping SDK as required by .keep file flag"
    exit $rc
  fi
  echo Cleanup on exit
  # Delete old SDK directory to not waste space
  [ -d "${DATA_DIR}/chromiumos-sdk" ] && sudo rm -rf ${DATA_DIR}/chromiumos-sdk && echo Old SDK deleted
  exit $rc
}

trap cleanup EXIT

# Check if branch is set
# You can check list of existing at: https://chromium.googlesource.com/chromiumos/manifest/+refs
if [ -z "$BRANCH" ]; then
  echo "ChromiumOS manifest snapshot generator"
  echo "Usage: $0 <branch>"
  echo "For example: release-R111-15329.B"
  exit 1
fi

echo "Preparing depot tools"
cd "/home/${USERNAME}/chromiumos"
if [ ! -d depot_tools ] ; then
  git clone --depth=1 https://chromium.googlesource.com/chromium/tools/depot_tools.git
fi
export PATH="/home/${USERNAME}/chromiumos/depot_tools:${PATH}"
cd ${DATA_DIR}

echo "Preparing environment, branch ${BRANCH}"
sudo mkdir -p chromiumos-sdk
sudo chown ${USERNAME} chromiumos-sdk
cd chromiumos-sdk
git config --global user.email "bot@kernelci.org"
git config --global user.name "KernelCI Bot"
git config --global color.ui false

echo "Installing dependencies"
sudo apt install -y less
echo "Initializing repo"
repo init --repo-url https://chromium.googlesource.com/external/repo --manifest-url https://chromium.googlesource.com/chromiumos/manifest --manifest-name default.xml --manifest-branch ${BRANCH}
echo "Syncing repo"
repo sync -j$(nproc)
echo "Generating manifest"
repo manifest -r -o cros-snapshot.xml
echo "Copying manifest"
mv cros-snapshot.xml /kernelci-core
