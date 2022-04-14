#!/bin/bash
set -e
BOARD=$1
BRANCH=$2
DATA_DIR=$(pwd)
USERNAME=$(/usr/bin/id -run)

function cleanup()
{
  rc=$?
  echo Cleanup on exit
  # Delete old SDK directory to not waste space
  [ -d "${DATA_DIR}/chromiumos-sdk" ] && sudo rm -rf ${DATA_DIR}/chromiumos-sdk && echo Old SDK deleted
  exit $rc
}

trap cleanup EXIT

echo Preparing environment, branch ${BRANCH}
sudo mkdir chromiumos-sdk
sudo chown user chromiumos-sdk
cd chromiumos-sdk
git config --global user.email "bot@kernelci.org"
git config --global user.name "KernelCI Bot"
git config --global color.ui false
repo init --repo-url https://chromium.googlesource.com/external/repo --manifest-url https://chromium.googlesource.com/chromiumos/manifest --manifest-name default.xml --manifest-branch ${BRANCH}
repo sync -j$(nproc)
echo Building SDK
cros_sdk --create

echo Board ${BOARD} setup
# Compiling ChromiumOS image
# Future possible option --profile=x, for example kernel-5_15, profiles are at /mnt/host/source/src/overlays/overlay-${BOARD}/profiles/
cros_sdk setup_board --board=${BOARD}

# Without workarounds hatch and octopus build failing
if [ "${BOARD}" == "hatch" ]; then
echo Patching hatch specific issue
sed -i 's/EC_BOARDS=()/EC_BOARDS=(hatch)/' src/third_party/chromiumos-overlay/eclass/cros-ec-board.eclass
fi
if [ "${BOARD}" == "octopus" ]; then
echo Patching octopus specific issue
sed -i s,'use fuzzer || die',"#use fuzzer || die", src/third_party/chromiumos-overlay/eclass/cros-ec-board.eclass
fi

# Add serial support
echo Add serial support
cros_sdk USE=pcserial ./build_packages --board=${BOARD}
cros_sdk USE="tty_console_ttyS0" emerge-"${BOARD}" chromeos-base/tty
echo Building image
cros_sdk ./build_image --enable_serial ttyS0 --board="${BOARD}" --boot_args "earlyprintk=serial,keep console=tty0" --noenable_rootfs_verification test

echo Moving artifacts
# Create artifacts dir and copy generated image and tast files
sudo mkdir -p "${DATA_DIR}/${BOARD}"
sudo cp "src/build/images/${BOARD}/latest/chromiumos_test_image.bin" "${DATA_DIR}/${BOARD}"
sudo tar -czf "${DATA_DIR}/${BOARD}/tast.tgz" -C ./chroot/usr/bin/ remote_test_runner tast
sudo chown -R "${USERNAME}" "${DATA_DIR}/${BOARD}"
gzip -1 "${DATA_DIR}/${BOARD}/chromiumos_test_image.bin"

# Probably redundant, but better safe than sorry
cleanup
