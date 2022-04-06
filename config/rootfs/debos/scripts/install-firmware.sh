#!/bin/bash

# Usage:
# install-firmware.sh [OPTIONS]
#
#     -v <version>                  version (tag, branch or commit) of the
#                                   linux-firmware repo to fetch
#     -f <file_1> ... <file_n>      files to install

set -e

FIRMWARE_SITE=https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git
FIRMWARE_DEFAULT_VERSION=d526e044bddaa2c2ad855c7296147e49be0ab03c

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
mkdir -p $TMP_REPO && cd $TMP_REPO
git init
git remote add origin $FIRMWARE_SITE
git fetch --depth 1 origin $version
git checkout FETCH_HEAD

for fw_file in "${files[@]}"
do
    cp --parents "$fw_file" $DEST
done

########################################################################
# Cleanup: remove downloaded firmware files
########################################################################
rm -rf $TMP_REPO
