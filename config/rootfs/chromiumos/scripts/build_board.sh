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

echo "Preparing environment, branch ${BRANCH}"
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

# Fetching current manifest snapshot
repo init -u https://github.com/kernelci/kernelci-core -b chromeos.kernelci.org -m "config/rootfs/chromiumos/cros-snapshot-$2.xml"
repo sync -j$(nproc)
echo Building SDK
cros_sdk --create

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

# Temporary workaround as chrome-icu build fails at 10/08/2022 due corrupt git cache
if [ ! -f .cache/distfiles/chrome-src/.gclient ]; then
  cros_sdk sync_chrome --tag=106.0.5249.134 --reset --gclient=/mnt/host/depot_tools/gclient /var/cache/chromeos-cache/distfiles/chrome-src --skip_cache
fi

echo "Building packages (${SERIAL})"
cros_sdk USE="tty_console_${SERIAL} pcserial" build_packages --board=${BOARD}

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

echo "Updating ownership"
sudo chown -R "${USERNAME}" "${DATA_DIR}/${BOARD}"

echo "Compressing image"
gzip -1 "${DATA_DIR}/${BOARD}/chromiumos_test_image.bin"

echo "Extracting additional artifacts"
sudo tar -cJf "${DATA_DIR}/${BOARD}/modules.tar.xz" -C ./chroot/build/${BOARD} lib/modules
sudo cp "./chroot/build/${BOARD}/boot/vmlinuz" "${DATA_DIR}/${BOARD}/bzImage"
sudo cp ./chroot/build/${BOARD}/boot/config* "${DATA_DIR}/${BOARD}/kernel.config"

echo "Extracting ${BOARD} specific artifacts"
case ${BOARD} in
    trogdor)
    # arm64 needs dtb to boot
    mkdir -p ${DATA_DIR}/${BOARD}/dtbs/qcom
    sudo cp ./chroot/build/${BOARD}/var/cache/portage/sys-kernel/chromeos-kernel-*/arch/arm64/boot/dts/qcom/*.dtb ${DATA_DIR}/${BOARD}/dtbs/qcom
    # ARM64 depthcharge need different kernel image file
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
