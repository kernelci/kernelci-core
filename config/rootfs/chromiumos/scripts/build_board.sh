#!/bin/sh
set -e
BOARD=$1
BRANCH=$2
DATA_DIR=$(pwd)

# Building SDK itself
if [ ! -d chromiumos-sdk ]; then
  sudo mkdir chromiumos-sdk
  sudo chown user chromiumos-sdk
  cd chromiumos-sdk
  git config --global user.email "bot@kernelci.org"
  git config --global user.name "KernelCI Bot"
  git config --global color.ui false
  repo init --repo-url https://chromium.googlesource.com/external/repo --manifest-url https://chromium.googlesource.com/chromiumos/manifest --manifest-name default.xml --manifest-branch ${BRANCH} --depth=1
  repo sync -j$(nproc)
  cros_sdk --create
else
  cd chromiumos-sdk
  # We might have different branch
  repo init --repo-url https://chromium.googlesource.com/external/repo --manifest-url https://chromium.googlesource.com/chromiumos/manifest --manifest-name default.xml --manifest-branch ${BRANCH} --depth=1
  repo sync -j$(nproc)
  cros_sdk --create
fi

# Compiling ChromiumOS image
# Future possible option --profile=x, for example kernel-5_15, profiles are at /mnt/host/source/src/overlays/overlay-${BOARD}/profiles/
cros_sdk setup_board --board=${BOARD} --force
# Add serial support
cros_sdk USE=pcserial ./build_packages --board=${BOARD}
cros_sdk USE="tty_console_ttyS0" emerge-${BOARD} chromeos-base/tty
cros_sdk ./build_image --enable_serial ttyS0 --board=${BOARD} --boot_args "earlyprintk=serial,keep console=tty0" --noenable_rootfs_verification test

# Create artifacts dir and copy generated image and tast files
sudo mkdir -p ${DATA_DIR}/${BOARD}
sudo cp src/build/images/${BOARD}/latest/chromiumos_test_image.bin ${DATA_DIR}/${BOARD}
sudo cp ./chroot/usr/bin/remote_test_runner ${DATA_DIR}/${BOARD}
sudo cp ./chroot/usr/bin/tast ${DATA_DIR}/${BOARD}

# Delete build directory
[ -d "${DATA_DIR}/chromiumos-sdk/chroot/build" ] && sudo rm -rf ${DATA_DIR}/chromiumos-sdk/chroot/build && echo Build directory deleted
