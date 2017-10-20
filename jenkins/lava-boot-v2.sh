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
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp kselftest --token ${API_TOKEN}
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_TBAKER_TOKEN}
elif [ ${LAB} = "lab-mhart" ] || [ ${LAB} = "lab-mhart-dev" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp simple --token ${API_TOKEN} --priority medium
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_MHART_TOKEN}
elif [ ${LAB} = "lab-collabora" ] || [ ${LAB} = "lab-collabora-dev" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp kselftest --token ${API_TOKEN} --priority medium
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_COLLABORA_TOKEN}
elif [ ${LAB} = "lab-baylibre" ]  || [ ${LAB} = "lab-baylibre-dev" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-be boot-kvm boot-kvm-uefi kselftest --token ${API_TOKEN} --priority medium
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_BAYLIBRE_TOKEN}
elif [ ${LAB} = "lab-baylibre-seattle" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-be boot-kvm boot-kvm-uefi kselftest --token ${API_TOKEN} --priority medium
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_BAYLIBRE_SEATTLE_TOKEN}
elif [ ${LAB} = "lab-free-electrons" ] || [ ${LAB} = "lab-free-electrons-dev" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN} --priority medium
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_FREE_ELECTRONS_TOKEN}
elif [ ${LAB} = "lab-broonie" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN}
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_BROONIE_TOKEN}
elif [ ${LAB} = "lab-embeddedbits" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN}
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_EMBEDDEDBITS_TOKEN}
elif [ ${LAB} = "lab-jsmoeller" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN}
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_JSMOELLER_TOKEN}
elif [ ${LAB} = "lab-pengutronix" ]; then
  python lava-v2-jobs-from-api.py --defconfigs ${DEFCONFIG_COUNT} --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN}
  python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_PENGUTRONIX_TOKEN}
fi
