#!/bin/bash
env

# Build 
./configs/frags/build ${arch}

# Publish
set -x
PUBLISH_PATH=images/rootfs/buildroot/$(git describe)/${arch}/base
ls -l output/images
(cd output/images; push-source.py --token ${API_TOKEN} --api ${API} --publish_path ${PUBLISH_PATH} --file *)
