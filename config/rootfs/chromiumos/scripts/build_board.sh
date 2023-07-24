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

# To generate manifest snapshot, install less by apt, then uncomment:
# repo init --repo-url https://chromium.googlesource.com/external/repo --manifest-url https://chromium.googlesource.com/chromiumos/manifest --manifest-name default.xml --manifest-branch ${BRANCH}
# repo sync -j$(nproc)
# repo manifest -r -o cros-snapshot.xml
# mv cros-snapshot.xml /kernelci-core
# exit


if [ -n "${VANILLA_MANIFEST}" ]; then
  echo "Fetching vanilla manifest ${VANILLA_MANIFEST}"
  repo init --repo-url https://chromium.googlesource.com/external/repo --manifest-url https://chromium.googlesource.com/chromiumos/manifest --manifest-name default.xml --manifest-branch ${VANILLA_MANIFEST}
else
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

# if board trogdor we need to revert patch early, here
if [ "${BOARD}" == "trogdor" ]; then
    # issue/284169814 revert caf6c399cb013fb44b767d32853a7ba181a59c23 in chromiumos/overlays/board-overlays
    echo "Reverting issue/284169814 commit caf6c399cb013fb44b767d32853a7ba181a59c23 for trogdor"
    cd src/overlays
    git revert caf6c399cb013fb44b767d32853a7ba181a59c23
    cd -
fi

# grunt/StoneyRidge kernel 4.14 broken, so switch to 5.10
sed -i 's/kernel-4_14/kernel-5_10/g' src/overlays/chipset-stnyridge/profiles/base/make.defaults

echo "Board ${BOARD} setup"
cros_sdk setup_board --board=${BOARD}

echo "Patching ${BOARD} specific issues"
case ${BOARD} in
    coral)
    sed ':a;N;$!ba;s/DEPEND="\n\tchromeos-base\/fibocom-firmware\n"/# DEPEND="\n\t# chromeos-base\/fibocom-firmware\n# "/g' -i src/overlays/overlay-coral/chromeos-base/modemfwd-helpers/modemfwd-helpers-0.0.1.ebuild
    sed -i s,'media-libs/apl-hotword-support','# media-libs/apl-hotword-support', src/overlays/overlay-coral/media-libs/lpe-support-topology/lpe-support-topology-0.0.1.ebuild
    sed -i s,'USE="${USE} cros_ec"','# USE="${USE} cros_ec"', src/overlays/baseboard-coral/profiles/base/make.defaults
    ;;
    dedede)
    grep -q "tpm2" src/overlays/baseboard-dedede/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2 cr50_onboard"' >>src/overlays/baseboard-dedede/profiles/base/make.defaults
    ;;
    hatch)
    sed -i 's/EC_BOARDS=()/EC_BOARDS=(hatch)/' src/third_party/chromiumos-overlay/eclass/cros-ec-board.eclass
    grep -q "tpm2" src/overlays/baseboard-hatch/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-hatch/profiles/base/make.defaults
    ;;
    nami)
    grep -q "tpm2" src/overlays/baseboard-nami/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-nami/profiles/base/make.defaults
    ;;
    octopus)
    sed -i s,'use fuzzer || die',"#use fuzzer || die", src/third_party/chromiumos-overlay/eclass/cros-ec-board.eclass
    # Workaround b/244460939 T38487 - octopus missing proper tpm USE flags
    grep -q "tpm2" src/overlays/baseboard-octopus/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-octopus/profiles/base/make.defaults
    ;;
    sarien)
    sed ':a;N;$!ba;s/DEPEND="\n\tchromeos-base\/fibocom-firmware\n"/# DEPEND="\n\t# chromeos-base\/fibocom-firmware\n# "/g' -i src/overlays/overlay-sarien/chromeos-base/modemfwd-helpers/modemfwd-helpers-0.0.1.ebuild
    ;;
    volteer)
    grep -q "tpm2" src/overlays/baseboard-volteer/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-volteer/profiles/base/make.defaults
    ;;
    zork)
    grep -q "tpm2" src/overlays/overlay-zork/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/overlay-zork/profiles/base/make.defaults
    ;;
    grunt)
    grep -q "tpm2" src/overlays/baseboard-grunt/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-grunt/profiles/base/make.defaults
    ;;
    *)
    echo "No issues found for this board"
    ;;
esac

# if environment variable SANDBOX_BUG is set, then we need to use sandbox workaround
# This is very strange floating bug that appears only on some builders
if [ -n "${SANDBOX_BUG}" ]; then
  echo "Applying sandbox workaround for Chromium"
  cros_sdk FEATURES="-usersandbox" USE="tty_console_${SERIAL} pcserial cr50_skip_update -builtin_fw_mali_g57" emerge-${BOARD} chromeos-chrome
fi

echo "Building packages (${SERIAL})"
# Disable `builtin_fw_mali_g57` flag as it is not required when `panfrost` is enabled
cros_sdk USE="tty_console_${SERIAL} pcserial cr50_skip_update -builtin_fw_mali_g57" \
	 build_packages --board=${BOARD}

echo "Building image (${SERIAL})"
cros_sdk ./build_image --enable_serial ${SERIAL} --board="${BOARD}" --boot_args "earlyprintk=serial,keep console=tty0" --noenable_rootfs_verification test

echo "Creating artifacts dir and copy generated image"
sudo mkdir -p "${DATA_DIR}/${BOARD}"
sudo cp "src/build/images/${BOARD}/latest/chromiumos_test_image.bin" "${DATA_DIR}/${BOARD}"

echo "Packing Tast files"
sudo tar -cf "${DATA_DIR}/${BOARD}/tast.tar" -C ./chroot/usr/bin/ remote_test_runner tast
sudo tar -uf "${DATA_DIR}/${BOARD}/tast.tar" -C ./chroot/usr/libexec/tast/bundles/remote/ cros
sudo gzip -9 "${DATA_DIR}/${BOARD}/tast.tar"
sudo mv "${DATA_DIR}/${BOARD}/tast.tar.gz" "${DATA_DIR}/${BOARD}/tast.tgz"

echo "Removing CR50 firmware from rootfs"
cd "${DATA_DIR}/${BOARD}"
# This is guestfish commands, even they are similar to bash, it is not shell
# rm-rf is for example guestfish specific command
sudo guestfish <<_EOF_
add chromiumos_test_image.bin
run
mount /dev/sda3 /
rm-rf /opt/google/cr50/firmware
_EOF_
# End of guestfish commands
cd -

echo "Updating ownership"
sudo chown -R "${USERNAME}" "${DATA_DIR}/${BOARD}"

echo "Compressing image"
gzip -1 "${DATA_DIR}/${BOARD}/chromiumos_test_image.bin"

echo "Extracting additional artifacts"
sudo tar -cJf "${DATA_DIR}/${BOARD}/modules.tar.xz" -C ./chroot/build/${BOARD} lib/modules
sudo cp "./chroot/build/${BOARD}/boot/vmlinuz" "${DATA_DIR}/${BOARD}/bzImage"
sudo cp ./chroot/build/${BOARD}/boot/config* "${DATA_DIR}/${BOARD}/kernel.config"
# Extract CR50 firmware, but dont crash in case it is missing
sudo mv ./chroot/build/${BOARD}/opt/google/cr50/firmware/* "${DATA_DIR}/${BOARD}/" || true

echo "Extracting ${BOARD} specific artifacts"
case ${BOARD} in
    trogdor)
    # arm64 needs dtb to boot
    mkdir -p ${DATA_DIR}/${BOARD}/dtbs/qcom
    sudo cp ./chroot/build/${BOARD}/var/cache/portage/sys-kernel/chromeos-kernel-*/arch/arm64/boot/dts/qcom/*.dtb ${DATA_DIR}/${BOARD}/dtbs/qcom
    # ARM64 depthcharge need different kernel image file
    sudo cp ./chroot/build/${BOARD}/boot/Image* "${DATA_DIR}/${BOARD}/Image"
    ;;
    asurada|jacuzzi|cherry|geralt)
    mkdir -p ${DATA_DIR}/${BOARD}/dtbs/mediatek
    sudo cp ./chroot/build/${BOARD}/var/cache/portage/sys-kernel/*kernel*/arch/arm64/boot/dts/mediatek/*.dtb \
	 ${DATA_DIR}/${BOARD}/dtbs/mediatek
    sudo cp ./chroot/build/${BOARD}/boot/Image* "${DATA_DIR}/${BOARD}/Image"
    ;;
    *)
    echo "No issues found for this board"
    ;;
esac


echo "Creating manifest file"
python3 "${SCRIPTPATH}/create_manifest.py" "${BOARD}" "${DATA_DIR}/${BOARD}"

# Probably redundant, but better safe than sorry
cleanup
