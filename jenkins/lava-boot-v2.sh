#!/bin/bash

set -x

if ! ./should-I-boot-this.py; then
  echo "Blacklisted"
  exit 0
fi

curl --silent --fail ${STORAGE}/${TREE}/${BRANCH}/${GIT_DESCRIBE}/${ARCH}_defconfig.count > ${ARCH}_defconfig.count
if [ $? == 0 ]; then
  DEFCONFIG_COUNT=`cat ${ARCH}_defconfig.count`
else
  DEFCONFIG_COUNT=0
fi

if [ ${LAB} = "lab-tbaker" ] || [ ${LAB} = "lab-tbaker-dev" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp kselftest --token ${API_TOKEN}
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_TBAKER_TOKEN} --lab ${LAB}
elif [ ${LAB} = "lab-mhart" ] || [ ${LAB} = "lab-mhart-dev" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp simple --token ${API_TOKEN} --priority medium
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_MHART_TOKEN} --lab ${LAB}
elif [ ${LAB} = "lab-collabora" ] || [ ${LAB} = "lab-collabora-dev" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp igt kselftest sleep usb v4l2 --token ${API_TOKEN} --priority medium
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_COLLABORA_TOKEN} --lab ${LAB}
elif [ ${LAB} = "lab-baylibre" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-kvm boot-kvm-uefi kselftest --token ${API_TOKEN} --priority medium
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_BAYLIBRE_TOKEN} --lab ${LAB}
elif [ ${LAB} = "lab-baylibre-dev" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-kvm boot-kvm-uefi kselftest --token ${API_TOKEN} --priority medium
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_BAYLIBRE_TOKEN} --lab ${LAB}
  # for dev lab, also send results to BayLibre kernelCI development backend
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback kernelci-dev-baylibre-callback --callback-url http://kernelci.dev.baylibre.com:8081 --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans simple usb --token ${API_TOKEN} --priority low
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_BAYLIBRE_TOKEN} --lab ${LAB}
elif [ ${LAB} = "lab-baylibre-seattle" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-kvm boot-kvm-uefi kselftest --token ${API_TOKEN} --priority medium
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_BAYLIBRE_SEATTLE_TOKEN} --lab ${LAB}
elif [ ${LAB} = "lab-free-electrons" ] || [ ${LAB} = "lab-free-electrons-dev" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN} --priority medium
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_FREE_ELECTRONS_TOKEN} --lab ${LAB}
elif [ ${LAB} = "lab-broonie" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN}
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_BROONIE_TOKEN} --lab ${LAB}
elif [ ${LAB} = "lab-embeddedbits" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN}
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_EMBEDDEDBITS_TOKEN} --lab ${LAB}
elif [ ${LAB} = "lab-jsmoeller" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN}
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_JSMOELLER_TOKEN} --lab ${LAB}
elif [ ${LAB} = "lab-pengutronix" ] || [ ${LAB} = "lab-pengutronix-dev" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN}
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_PENGUTRONIX_TOKEN} --lab ${LAB}
elif [ ${LAB} = "lab-linaro-lkft" ] || [ ${LAB} = "lab-linaro-lkft-dev" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot --token ${API_TOKEN} --priority low
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_LINARO_LKFT_TOKEN} --lab ${LAB}
elif [ ${LAB} = "lab-theobroma-systems" ] || [ ${LAB} = "lab-theobroma-systems-dev" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot kselftest --token ${API_TOKEN}
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_THEOBROMA_SYSTEMS_TOKEN} --lab ${LAB}
fi
