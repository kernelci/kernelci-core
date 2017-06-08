#!/bin/bash

set -x

echo "Executing build-complete of (${TREE_NAME}/${BRANCH}) for arch ${ARCH}"

bash -x ./kernelci-build/build-complete.sh