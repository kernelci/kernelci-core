#!/bin/bash

# Copyright (C) 2019 Linaro Limited
# Author: Matt Hart <matthew.hart@linaro.org>
#
# Copyright (C) 2021, 2022 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

# Build all of the Docker images for kernelci
# -n = disable cache (for when rebuilding a moving target image e.g. clang)
# -p = push to Docker Hub
# -q = make the builds quiet
# -t = the prefix to use in docker tags (default is kernelci/)

set -e

tag_px='kernelci/'

options='npqt:'
while getopts $options option
do
  case $option in
    n )  cache_args="--no-cache";;
    p )  push=true;;
    q )  quiet="--quiet";;
    t )  tag_px=$OPTARG;;
    \? )
        echo "Invalid Option: -$OPTARG" 1>&2
        exit 1
        ;;
    : )
        echo "Invalid Option: -$OPTARG requires an argument" 1>&2
        exit 1
        ;;
  esac
done
shift $((OPTIND -1))

all_targets="\
build-base \
buildroot \
compilers \
debos \
"

if [ -n "$*" ]; then
    targets="$*"
else
    targets="$all_targets"
fi
echo "targets: $targets"


docker_build_and_tag() {
    local target="$1"
    local extra_args="$2"
    local tag=${tag_px}"$target"

    echo "Building [$tag]"

    docker build \
           --build-arg PREFIX="$tag_px" \
           ${quiet} \
           ${cache_args} \
           ${extra_args} \
           ${target} \
           -t ${tag}

    if [ "x${push}" == "xtrue" ]
    then
        echo "Pushing [$1]"
        docker push "$tag"
    fi
}

for target in $targets; do
    if [ "$target" = "compilers" ]; then
        docker_build_and_tag clang-base
        for cc in {gcc,clang}-*
        do
            docker_build_and_tag "$cc"
        done
    else
        docker_build_and_tag "$target"
    fi
done

exit 0
