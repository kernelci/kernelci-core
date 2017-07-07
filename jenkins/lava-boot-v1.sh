#!/bin/bash

set -x 

if [ ${LAB} = "lab-tbaker" ]; then
	python lava-kernel-ci-job-creator.py ${STORAGE}/$TREE/$BRANCH/$GIT_DESCRIBE/ --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --arch $ARCH --jobs ${LAB}
	python lava-job-runner.py --username kernel-ci --token ${LAVA_TOKEN_TBAKER} --server http://lava.kernelci.org/RPC2/ --stream /anonymous/kernel-ci/ --poll kernel-ci.json --timeout 7200
	python lava-report.py --boot results/kernel-ci.json --lab ${LAB} --token ${API_TOKEN_TBAKER} --api ${API}
elif [ ${LAB} = "lab-mhart" ]; then
	python lava-kernel-ci-job-creator.py ${STORAGE}/$TREE/$BRANCH/$GIT_DESCRIBE/ --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --arch $ARCH --jobs ${LAB}
	python lava-job-runner.py --username kernel-ci --token ${LAVA_TOKEN_MHART} --server http://lava.streamtester.net/RPC2/ --stream /anonymous/kernel-ci/ --poll kernel-ci.json --timeout 7200
	python lava-report.py --boot results/kernel-ci.json --lab ${LAB} --token ${API_TOKEN_MHART} --api ${API}
elif [ ${LAB} = "lab-collabora" ]; then
	python lava-kernel-ci-job-creator.py ${STORAGE}/$TREE/$BRANCH/$GIT_DESCRIBE/ --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --arch $ARCH --jobs ${LAB} --priority medium
	python lava-job-runner.py --username kernel-ci --token ${LAVA_TOKEN_COLLABORA} --server https://lava.collabora.co.uk/RPC2/ --stream /anonymous/kernel-ci/ --poll kernel-ci.json --timeout 7200
	python lava-report.py --boot results/kernel-ci.json --lab ${LAB} --token ${API_TOKEN_COLLABORA} --api ${API}
elif [ ${LAB} = "lab-cambridge" ]; then
	python lava-kernel-ci-job-creator.py ${STORAGE}/$TREE/$BRANCH/$GIT_DESCRIBE/ --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --arch $ARCH --jobs ${LAB} --targets mustang hi3716cv200 juno beaglebone-black kvm d01 arndale highbank
	python lava-job-runner.py --username kernel-ci --token ${LAVA_TOKEN_CAMBRIDGE} --server https://validation.linaro.org/RPC2/ --stream /anonymous/kernel-ci/ --poll kernel-ci.json --timeout 7200
	python lava-report.py --boot results/kernel-ci.json --lab ${LAB} --token ${API_TOKEN_CAMBRIDGE} --api ${API}
elif [ ${LAB} = "lab-baylibre-seattle" ]; then
	python lava-kernel-ci-job-creator.py ${STORAGE}/$TREE/$BRANCH/$GIT_DESCRIBE/ --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --arch $ARCH --jobs ${LAB}
	python lava-job-runner.py --username kernel-ci --token ${LAVA_TOKEN_BAYLIBRE_SEATTLE} --server http://lava.ished.com/RPC2/ --stream /anonymous/kernel-ci/ --poll kernel-ci.json --timeout 7200
	python lava-report.py --boot results/kernel-ci.json --lab ${LAB} --token ${API_TOKEN_BAYLIBRE_SEATTLE} --api ${API}
elif [ ${LAB} = "lab-embeddedbits" ]; then
	python lava-kernel-ci-job-creator.py ${STORAGE}/$TREE/$BRANCH/$GIT_DESCRIBE/ --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --arch $ARCH --jobs ${LAB} --targets panda-es zynq-zc702 omap3-overo-storm-tobi imx6q-sabrelite
	python lava-job-runner.py --username kernel-ci --token ${LAVA_TOKEN_EMBEDDED_BITS} --server http://kernelci.embedded-bits.co.uk/RPC2/ --stream /anonymous/kernel-ci/ --poll kernel-ci.json --timeout 7200
	python lava-report.py --boot results/kernel-ci.json --lab ${LAB} --token ${API_TOKEN_EMBEDDED_BITS} --api ${API}
elif [ ${LAB} = "lab-jsmoeller" ]; then
	python lava-kernel-ci-job-creator.py ${STORAGE}/$TREE/$BRANCH/$GIT_DESCRIBE/ --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --arch $ARCH --jobs ${LAB}
	python lava-job-runner.py --username kernelciuser --token ${LAVA_TOKEN_JSMOELLER} --server https://88.198.106.157/mylava/RPC2/ --stream /anonymous/kernel-ci/ --poll kernel-ci.json --timeout 7200
	python lava-report.py --boot results/kernel-ci.json --lab ${LAB} --token ${API_TOKEN_JSMOELLER} --api ${API}
elif [ ${LAB} = "lab-baylibre" ]; then
	python lava-kernel-ci-job-creator.py ${STORAGE}/$TREE/$BRANCH/$GIT_DESCRIBE/ --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --arch $ARCH --jobs ${LAB}
	python lava-job-runner.py --username kernel-ci --token ${LAVA_TOKEN_BAYLIBRE} --server http://lava.baylibre.com:10080/RPC2/ --stream /anonymous/kernel-ci/ --poll kernel-ci.json --timeout 7200
	python lava-report.py --boot results/kernel-ci.json --lab ${LAB} --token ${API_TOKEN_BAYLIBRE} --api ${API}
elif [ ${LAB} = "lab-pengutronix" ]; then
	python lava-kernel-ci-job-creator.py ${STORAGE}/$TREE/$BRANCH/$GIT_DESCRIBE/ --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --arch $ARCH --jobs ${LAB}
	python lava-job-runner.py --username kernel-ci --token ${LAVA_TOKEN_PENGUTRONIX} --server https://hekla.openlab.pengutronix.de/RPC2/ --stream /anonymous/kernel-ci/ --poll kernel-ci.json --timeout 7200
	python lava-report.py --boot results/kernel-ci.json --lab ${LAB} --token ${API_TOKEN_PENGUTRONIX} --api ${API}
elif [ ${LAB} = "lab-free-electrons" ]; then
	python lava-kernel-ci-job-creator.py ${STORAGE}/$TREE/$BRANCH/$GIT_DESCRIBE/ --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --arch $ARCH --jobs ${LAB} --priority medium
	python lava-job-runner.py --username kernel-ci --token ${LAVA_TOKEN_FREE_ELECTRONS} --server https://lab.free-electrons.com/RPC2/ --stream /anonymous/kernel-ci/ --poll kernel-ci.json --timeout 7200
	python lava-report.py --boot results/kernel-ci.json --lab ${LAB} --token ${API_TOKEN_FREE_ELECTRONS} --api ${API}
elif [ ${LAB} = "lab-broonie" ]; then
	python lava-kernel-ci-job-creator.py ${STORAGE}/$TREE/$BRANCH/$GIT_DESCRIBE/ --plans boot boot-be boot-kvm boot-kvm-uefi boot-nfs boot-nfs-mp --arch $ARCH --jobs ${LAB}
	python lava-job-runner.py --username kernel-ci --token ${LAVA_TOKEN_BROONIE} --server http://lava.sirena.org.uk/RPC2/ --stream /anonymous/kernel-ci/ --poll kernel-ci.json --timeout 7200
	python lava-report.py --boot results/kernel-ci.json --lab ${LAB} --token ${API_TOKEN_BROONIE} --api ${API}
fi