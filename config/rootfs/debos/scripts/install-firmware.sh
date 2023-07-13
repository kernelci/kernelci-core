#!/bin/bash

# Usage:
# install-firmware.sh [OPTIONS]
#
#     -v <version>                  version (tag, branch or commit) of the
#                                   linux-firmware repo to fetch
#     -f <file_1> ... <file_n>      files to install

set -e

FIRMWARE_SITE=https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git
FIRMWARE_DEFAULT_VERSION=HEAD

version=""
files=()

while getopts ":v:f:" opt
do
    case $opt in
        v ) version=$OPTARG
            ;;
        f ) files=("$OPTARG")
            until [[ $(eval "echo \${$OPTIND}") =~ ^-.* ]] || [ -z $(eval "echo \${$OPTIND}") ]; do
                files+=($(eval "echo \${$OPTIND}"))
                OPTIND=$((OPTIND + 1))
            done
            ;;
    esac
done

if [[ "$version" == "" ]]; then
    version=$FIRMWARE_DEFAULT_VERSION
fi

DEST=${ROOTDIR}/lib/firmware
mkdir -p $DEST

# Because the linux-firmware repo is very big, we use the following
# git init hack to fetch a single shallow commit to minimize time,
# space and network bandwidth
TMP_REPO=/tmp/linux-firmware
# As we cannot use git "as-is" we need to "process" git to
# intermediate directory by using copy-firmware.sh script
TMP_FW=/tmp/linux-firmware-parsed
mkdir -p $TMP_FW
mkdir -p $TMP_REPO && cd $TMP_REPO

git init
git remote add origin $FIRMWARE_SITE
git fetch --depth 1 origin $version
git checkout FETCH_HEAD

./copy-firmware.sh ${TMP_FW}
cd ${TMP_FW}

for fw_file in "${files[@]}"
do
    cp --parents "$fw_file" $DEST
done

########################################################################
# Cleanup: remove downloaded firmware files
########################################################################
rm -rf $TMP_REPO
rm -rf $TMP_FW
