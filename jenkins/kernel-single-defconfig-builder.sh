#!/bin/bash

set -x


echo "Executing build of ${TREE} (${TREE_NAME}/${BRANCH}/${GIT_DESCRIBE} (${GIT_DESCRIBE_VERBOSE}) ) for arch ${ARCH} and defconfig ${defconfig}"
echo "Uploading to ${API}"

# Scripts are in the parent directory, add it to the path.
export PATH=${WORKSPACE}/kernelci-build:${PATH}

wget_retry.sh ${SRC_TARBALL}
if [ $? != 0 ]
then
    echo "Couldnt fetch the source tarball"
    exit 2
fi

tar -zxf linux-src.tar.gz
if [ $? != 0 ]
then
    echo "Extracting the source tarball failed"
    exit 2
fi

echo TREE=$TREE
echo TREE_NAME=$TREE_NAME
echo BRANCH=$BRANCH
echo GIT_DESCRIBE=$GIT_DESCRIBE
echo GIT_DESCRIBE_VERBOSE=$GIT_DESCRIBE_VERBOSE
echo COMMIT_ID=$COMMIT_ID
echo ARCH=$ARCH
echo defconfig=$defconfig
echo PUBLISH=$PUBLISH
echo EMAIL=$EMAIL
echo SRC_TARBALL=$SRC_TARBALL
echo API=$API


# since workspace is wiped clean after each build, ccache is pointless
export CCACHE_DISABLE=true

# Convert defconfig of form "foo+bar" into "foo -c bar"
defconfig_translated=`echo ${defconfig} | sed 's/\+/ \-c /g'`

# Build kernel/modules and install (default: ./_install_ dir)
export LANG=C
#export ARCH=${arch}
export ARCH=${ARCH}
if [ $PUBLISH != true ]; then
    build.py -i -c ${defconfig_translated}
else
    build.py -i -e -c ${defconfig_translated}
fi
RC=$?

# Remove the build output (important stuff in _install_ dir)
rm -rf build

echo "Kernel build result: ${RC}"
echo ${RC} > build.result

# Always return success here so pass/fail results can still be published
exit 0
