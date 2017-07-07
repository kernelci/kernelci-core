#!/bin/bash

set -x

if [ ${LAB} = "lab-tbaker" ] || [ ${LAB} = "lab-tbaker-dev" ]; then
	python lava-v2-jobs-from-api.py --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN}
    python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_TBAKER_TOKEN} --server http://lava.kernelci.org/RPC2/
elif [ ${LAB} = "lab-mhart" ] || [ ${LAB} = "lab-mhart-dev" ]; then
	python lava-v2-jobs-from-api.py --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp kselftest --token ${API_TOKEN}
    python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_MHART_TOKEN} --server http://lava.streamtester.net/RPC2/
elif [ ${LAB} = "lab-collabora" ] || [ ${LAB} = "lab-collabora-dev" ]; then
	python lava-v2-jobs-from-api.py --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans  boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN} --priority medium
    python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_COLLABORA_TOKEN} --server https://lava.collabora.co.uk/RPC2/
elif [ ${LAB} = "lab-baylibre" ]; then
	python lava-v2-jobs-from-api.py --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans  boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN}
    python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_BAYLIBRE_TOKEN} --server http://lava.baylibre.com:10080/RPC2/
elif [ ${LAB} = "lab-baylibre-seattle" ]; then
	python lava-v2-jobs-from-api.py --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans  boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN}
    python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_BAYLIBRE_SEATTLE_TOKEN} --server http://lava.ished.com/RPC2/
elif [ ${LAB} = "lab-free-electrons" ] || [ ${LAB} = "lab-free-electrons-dev" ]; then
	python lava-v2-jobs-from-api.py --callback ${CALLBACK} --api ${API} --storage ${STORAGE} --lab ${LAB} --describe ${GIT_DESCRIBE} --tree ${TREE} --branch ${BRANCH} --arch ${ARCH} --plans  boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --token ${API_TOKEN} --priority medium
    python lava-v2-submit-jobs.py --username kernel-ci --jobs ${LAB} --token ${LAVA_FREE_ELECTRONS_TOKEN} --server https://lab.free-electrons.com/RPC2/
fi    