#!/bin/bash
set -e
BOARD=$1
BRANCH=$2
SERIAL=$3
DATA_DIR=$(pwd)
OUT_DIR="out"
USERNAME=$(/usr/bin/id -run)
SCRIPT=$(realpath "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

VERSION=$(echo $BRANCH | sed 's/^.*-R\([[:digit:]]*\)-.*$/\1/')
if [ $VERSION -lt 120 ]; then
    OUT_DIR="chroot"
fi

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

# if VANILLA_MANIFEST is set, update BRANCH
if [ -n "${VANILLA_MANIFEST}" ]; then
  BRANCH=${VANILLA_MANIFEST}
fi

# Verify if all fixup files exist
if [ ! -f "${SCRIPTPATH}/fixes/presetup-${BRANCH}.sh" ]; then
  echo "WARNING: fixes/presetup-${BRANCH}.sh not found, please check if you need to apply any workarounds or remove old ones"
  echo "If you are doing uprev, take in consideration this warning(make sure old workarounds still needed or already fixed) and comment it out"
  echo "Add new ones, and when completed, update this warning to new release"
  echo "For example: touch kernelci-core/config/rootfs/chromiumos/scripts/fixes/presetup-${BRANCH}.sh"
  exit 1
fi
if [ ! -f "${SCRIPTPATH}/fixes/packagefix-${BRANCH}.sh" ]; then
  echo "WARNING: fixes/packagefix-${BRANCH}.sh not found, please check if you need to apply any workarounds or remove old ones"
  echo "If you are doing uprev, take in consideration this warning(make sure old workarounds still needed or already fixed) and comment it out"
  echo "Add new ones, and when completed, update this warning to new release"
  echo "For example: touch kernelci-core/config/rootfs/chromiumos/scripts/fixes/packagefix-${BRANCH}.sh"
  exit 1
fi

echo "Preparing depot tools"
cd "/home/${USERNAME}/chromiumos"
if [ ! -d depot_tools ] ; then
  git clone --depth=1 https://chromium.googlesource.com/chromium/tools/depot_tools.git
fi
export PATH="/home/${USERNAME}/chromiumos/depot_tools:${PATH}"
cd ${DATA_DIR}

echo "Preparing environment"
sudo mkdir -p chromiumos-sdk
sudo chown ${USERNAME} chromiumos-sdk
cd chromiumos-sdk
git config --global user.email "bot@kernelci.org"
git config --global user.name "KernelCI Bot"
git config --global color.ui false

if [ -n "${VANILLA_MANIFEST}" ]; then
  echo "Fetching vanilla manifest ${VANILLA_MANIFEST}"
  repo init --repo-url https://chromium.googlesource.com/external/repo --manifest-url https://chromium.googlesource.com/chromiumos/manifest --manifest-name default.xml --manifest-branch ${VANILLA_MANIFEST}
else
  # Ensure file ownership issues won't get in the way
  git config --global safe.directory /kernelci-core

  if [ -z "${KCICORE_BRANCH}" ]; then
    KCICORE_BRANCH="$(git -C /kernelci-core branch --show-current 2>/dev/null || true)"
  fi

  if [ -z "${KCICORE_URL}" ]; then
    KCICORE_URL="$(git -C /kernelci-core remote get-url origin 2>/dev/null || true)"
  fi

  if [ -z "${KCICORE_URL}" ] || [ -z "${KCICORE_BRANCH}" ]; then
    KCICORE_URL="https://github.com/kernelci/kernelci-core"
    KCICORE_BRANCH="chromeos.kernelci.org"
  elif echo "${KCICORE_URL}" | grep -q "^git@"; then
    # Transform repo URL to its https:// equivalent if needed
    KCICORE_URL="$(echo ${KCICORE_URL} | sed -e 's%:%/%g' -e 's%^git@%https://%')"
  fi

  echo "Fetching KernelCI manifest snapshot $2"
  repo init -u "${KCICORE_URL}" -b "${KCICORE_BRANCH}" -m "config/rootfs/chromiumos/cros-snapshot-$2.xml"
fi

repo sync -j$(nproc)
echo Building SDK
cros_sdk --create

echo "Applying presetup-${BRANCH}.sh"
source "${SCRIPTPATH}/fixes/presetup-${BRANCH}.sh"

echo "Board ${BOARD} setup"
cros_sdk setup_board --board=${BOARD}

echo "Applying fixes for ${BRANCH} packages"
source "${SCRIPTPATH}/fixes/packagefix-${BRANCH}.sh"

echo "Building packages (${SERIAL})"
# Disable `builtin_fw_mali_g57` flag as it is not required when `panfrost` is enabled
cros_sdk USE="tty_console_${SERIAL} pcserial cr50_skip_update -builtin_fw_mali_g57" \
	 build_packages --board=${BOARD}

echo "Building image (${SERIAL})"
cros_sdk build_image --enable_serial ${SERIAL} --board="${BOARD}" --boot_args "earlyprintk=serial,keep console=tty0" --noenable_rootfs_verification test

echo "Creating artifacts dir and copy generated image"
sudo mkdir -p "${DATA_DIR}/${BOARD}"
sudo cp "src/build/images/${BOARD}/latest/chromiumos_test_image.bin" "${DATA_DIR}/${BOARD}"

echo "Applying postbuild-${BRANCH}.sh"
source "${SCRIPTPATH}/fixes/postbuild-${BRANCH}.sh"

echo "Packing Tast files"
sudo tar -cf "${DATA_DIR}/${BOARD}/tast.tar" -C ./chroot/usr/bin/ remote_test_runner tast
sudo tar -uf "${DATA_DIR}/${BOARD}/tast.tar" -C ./chroot/usr/libexec/tast/bundles/remote/ cros
sudo gzip -9 "${DATA_DIR}/${BOARD}/tast.tar"
sudo mv "${DATA_DIR}/${BOARD}/tast.tar.gz" "${DATA_DIR}/${BOARD}/tast.tgz"

echo "Removing CR50/TI50 firmware from rootfs"
cd "${DATA_DIR}/${BOARD}"
# This is guestfish commands, even they are similar to bash, it is not shell
# rm-rf is for example guestfish specific command
sudo guestfish <<_EOF_
add chromiumos_test_image.bin
run
mount /dev/sda3 /
rm-rf /opt/google/cr50/firmware
rm-rf /opt/google/ti50/firmware
write /usr/lib/tmpfiles.d/kernelci.conf "f= /run/dont-modify-ps1-for-testing"
_EOF_
# End of guestfish commands
cd -

echo "Updating ownership"
sudo chown -R "${USERNAME}" "${DATA_DIR}/${BOARD}"

echo "Compressing image"
gzip -1 --force "${DATA_DIR}/${BOARD}/chromiumos_test_image.bin"

echo "Extracting additional artifacts"
sudo tar -cJf "${DATA_DIR}/${BOARD}/modules.tar.xz" -C ./${OUT_DIR}/build/${BOARD} lib/modules
sudo cp ./${OUT_DIR}/build/${BOARD}/boot/config* "${DATA_DIR}/${BOARD}/kernel.config"
# Extract CR50/TI50 firmware, but dont crash in case it is missing
sudo mv ./${OUT_DIR}/build/${BOARD}/opt/google/{cr,ti}50/firmware/* "${DATA_DIR}/${BOARD}/" > /dev/null 2>&1 || true

# Identify baseboard and chipset
BASEBOARD="$(grep -m1 baseboard ./src/overlays/overlay-${BOARD}/profiles/base/parent | sed 's/:.*//')"
if [ -z "${BASEBOARD}" ]; then
    # Some overlays (e.g. skyrim) directly refer to the chipset overlay,
    # not to an intermediate baseboard
    BASEBOARD="overlay-${BOARD}"
fi
CHIPSET="$(grep -m1 chipset ./src/overlays/${BASEBOARD}/profiles/base/parent | sed 's/:.*//')"
# Source chipset config for $CHROMEOS_KERNEL_ARCH
. ./src/overlays/${CHIPSET}/profiles/base/make.defaults

echo "Extracting ${BOARD} specific artifacts"
if [ "${CHROMEOS_KERNEL_ARCH}" = "arm64" ]; then
    for vendor in mediatek qualcomm; do
        if echo "${USE}" | grep -q "${vendor}_cpu"; then
            BOARD_VENDOR="${vendor}"
            break
        fi
    done

    if [ "${BOARD_VENDOR}" = "qualcomm" ]; then
        BOARD_VENDOR="qcom"
    fi

    # Source the base config for $CHROMEOS_DTBS
    . ./src/overlays/${BASEBOARD}/profiles/base/make.defaults

    # ARM64 needs dtb to boot
    mkdir -p ${DATA_DIR}/${BOARD}/dtbs/${BOARD_VENDOR}
    sudo cp ./${OUT_DIR}/build/${BOARD}/var/cache/portage/sys-kernel/*kernel*/arch/arm64/boot/dts/${BOARD_VENDOR}/${CHROMEOS_DTBS} \
            ${DATA_DIR}/${BOARD}/dtbs/${BOARD_VENDOR}

    # Copy kernel image for ARM64 board
    sudo cp ./${OUT_DIR}/build/${BOARD}/boot/Image* "${DATA_DIR}/${BOARD}/Image"
else
    # Copy kernel image for x86-64 board
    sudo cp "./${OUT_DIR}/build/${BOARD}/boot/vmlinuz" "${DATA_DIR}/${BOARD}/bzImage"
fi

echo "Creating artifacts manifest file"
python3 "${SCRIPTPATH}/create_artifacts_manifest.py" "${BOARD}" "${DATA_DIR}/${BOARD}"

# Probably redundant, but better safe than sorry
cleanup
