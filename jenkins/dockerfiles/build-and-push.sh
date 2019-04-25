#!/bin/bash

# Copyright (C) 2019 Linaro Limited
# Author: Matt Hart <matthew.hart@linaro.org>
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

# Rebuild all of the docker images for kernelci
# You will need push privileges to kernelci namespace on dockerhub
# -n = disable cache (for when rebuilding a moving target image e.g. clang-8)
# -p = push to dockerhub
# -b = also rebuild build-base
# -d = also rebuild debos
# -q = make the builds quiet
# -d = the docker namespace/account to build for (default is kernelci)

set -e
dockerhub='kernelci'

options='npbdqh:'
while getopts $options option
do
  case $option in
    n )  cache_args="--no-cache";;
    p )  push=true;;
    b )  base=true;;
    d )  debos=true;;
    q )  quiet="--quiet";;
    h )  dockerhub=$OPTARG;;
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

echo_build() {
  echo "Building [$1]"
}

echo_push() {
  echo "Pushing [$1]"
}


if [ "x${base}" == "xtrue" ]
then
  tag=${dockerhub}/build-base
  echo_build $tag
  docker build ${quiet} ${cache_args} build-base -t $tag
  if [ "x${push}" == "xtrue" ]
  then
    echo_push $tag
    docker push $tag
  fi
fi

for c in {gcc,clang}-*
do
  tag=${dockerhub}/build-$c
  echo_build $tag
  docker build ${quiet} ${cache_args} $c -t $tag
  if [ "x${push}" == "xtrue" ]
  then
    echo_push $tag
    docker push $tag
  fi
done

if [ "x${debos}" == "xtrue" ]
then
  tag=${dockerhub}/debos
  echo_build $tag
  docker build ${quiet} ${cache_args} debos -t $tag
  if [ "x${push}" == "xtrue" ]
  then
    echo_push $tag
    docker push $tag
  fi
fi
