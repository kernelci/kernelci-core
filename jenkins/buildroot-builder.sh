#!/bin/bash
env

# Build 
./configs/frags/build ${arch} ${frag}

# Publish
set -x
PUBLISH_PATH=images/rootfs/buildroot/$(git describe)/${arch}/${frag}
ls -l output/images
(cd output/images; push-source.py --token ${API_TOKEN} --api ${API} --publish_path ${PUBLISH_PATH} --file *)
