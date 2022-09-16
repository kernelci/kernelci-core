#!/bin/bash
set -e
BOARD=$1
BRANCH=$2
SERIAL=$3
DATA_DIR=$(pwd)
USERNAME=$(/usr/bin/id -run)
SCRIPT=$(realpath "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

function cleanup()
{
  rc=$?
  echo Cleanup on exit
  # Delete old SDK directory to not waste space
  [ -d "${DATA_DIR}/chromiumos-sdk" ] && sudo rm -rf ${DATA_DIR}/chromiumos-sdk && echo Old SDK deleted
  exit $rc
}

trap cleanup EXIT

echo "Preparing depot tools"
cd "/home/${USERNAME}/chromiumos"
git clone --depth=1 https://chromium.googlesource.com/chromium/tools/depot_tools.git
export PATH="/home/${USERNAME}/chromiumos/depot_tools:${PATH}"
cd ${DATA_DIR}

echo "Preparing environment, branch ${BRANCH}"
sudo mkdir chromiumos-sdk
sudo chown ${USERNAME} chromiumos-sdk
cd chromiumos-sdk
git config --global user.email "bot@kernelci.org"
git config --global user.name "KernelCI Bot"
git config --global color.ui false

# To generate manifest snapshot:
# repo init --repo-url https://chromium.googlesource.com/external/repo --manifest-url https://chromium.googlesource.com/chromiumos/manifest --manifest-name default.xml --manifest-branch ${BRANCH}
# repo manifest -r -o cros-snapshot.xml

# Fetching current manifest snapshot
repo init -u https://github.com/kernelci/kernelci-core -b chromeos.kernelci.org -m "config/rootfs/chromiumos/cros-snapshot-$2.xml"
repo sync -j$(nproc)
echo Building SDK
cros_sdk --create

echo "Board ${BOARD} setup"
# Compiling ChromiumOS image
# Future possible option --profile=x, for example kernel-5_15, profiles are at /mnt/host/source/src/overlays/overlay-${BOARD}/profiles/
cros_sdk setup_board --board=${BOARD}

# Without workarounds hatch and octopus build failing
if [ "${BOARD}" == "hatch" ]; then
echo "Patching hatch specific issue"
sed -i 's/EC_BOARDS=()/EC_BOARDS=(hatch)/' src/third_party/chromiumos-overlay/eclass/cros-ec-board.eclass
fi
if [ "${BOARD}" == "octopus" ]; then
echo "Patching octopus specific issue"
sed -i s,'use fuzzer || die',"#use fuzzer || die", src/third_party/chromiumos-overlay/eclass/cros-ec-board.eclass
fi

if [ "${BOARD}" == "coral" ]; then
echo "Patching coral specific issues"
sed ':a;N;$!ba;s/DEPEND="\n\tchromeos-base\/fibocom-firmware\n"/# DEPEND="\n\t# chromeos-base\/fibocom-firmware\n# "/g' -i src/overlays/overlay-coral/chromeos-base/modemfwd-helpers/modemfwd-helpers-0.0.1.ebuild
sed -i s,'media-libs/apl-hotword-support','# media-libs/apl-hotword-support', src/overlays/overlay-coral/media-libs/lpe-support-topology/lpe-support-topology-0.0.1.ebuild
sed -i s,'USE="${USE} cros_ec"','# USE="${USE} cros_ec"', src/overlays/baseboard-coral/profiles/base/make.defaults
fi

# Temporary workaround as chrome-icu build fails at 10/08/2022 due corrupt git cache
cros_sdk sync_chrome --tag=102.0.5005.171 --reset --gclient=/mnt/host/depot_tools/gclient /var/cache/chromeos-cache/distfiles/chrome-src --skip_cache

# Add serial support
echo "Add serial ${SERIAL} support"
cros_sdk USE=pcserial build_packages --board=${BOARD}
cros_sdk USE="tty_console_${SERIAL}" emerge-"${BOARD}" chromeos-base/tty
echo "Building image (${SERIAL})"
cros_sdk ./build_image --enable_serial ${SERIAL} --board="${BOARD}" --boot_args "earlyprintk=serial,keep console=tty0" --noenable_rootfs_verification test

echo "Moving artifacts"
# Create artifacts dir and copy generated image and tast files
sudo mkdir -p "${DATA_DIR}/${BOARD}"
sudo cp "src/build/images/${BOARD}/latest/chromiumos_test_image.bin" "${DATA_DIR}/${BOARD}"
sudo tar -czf "${DATA_DIR}/${BOARD}/tast.tgz" -C ./chroot/usr/bin/ remote_test_runner tast
sudo chown -R "${USERNAME}" "${DATA_DIR}/${BOARD}"
gzip -1 "${DATA_DIR}/${BOARD}/chromiumos_test_image.bin"
sudo tar -cJf "${DATA_DIR}/${BOARD}/modules.tar.xz" -C ./chroot/build/${BOARD} lib/modules
sudo cp "./chroot/build/${BOARD}/boot/vmlinuz" "${DATA_DIR}/${BOARD}/bzImage"
sudo cp ./chroot/build/${BOARD}/boot/config* "${DATA_DIR}/${BOARD}/kernel.config"
python3 "${SCRIPTPATH}/create_manifest.py" "${BOARD}" "${DATA_DIR}/${BOARD}"

# Probably redundant, but better safe than sorry
cleanup
