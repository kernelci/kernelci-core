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
# -b = also rebuild kernel builders
# -d = also rebuild debos
# -r = also rebuild buildroot
# -i = also rebuild dt-validation
# -q = make the builds quiet
# -Q = also rebuild qemu docker image
# -t = the prefix to use in docker tags (default is kernelci/)

set -e
tag_px='kernelci/'

options='npbdrikqQt:'
while getopts $options option
do
  case $option in
    n )  cache_args="--no-cache";;
    p )  push=true;;
    b )  builders=true;;
    d )  debos=true;;
    r )  buildroot=true;;
    i )  dt_validation=true;;
    k )  k8s=true;;
    q )  quiet="--quiet";;
    Q )  qemu=true;;
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

echo_build() {
  echo "Building [$1]"
}

echo_push() {
  echo "Pushing [$1]"
}


if [ "x${builders}" == "xtrue" ]
then
  tag=${tag_px}build-base
  echo_build $tag
  docker build ${quiet} ${cache_args} build-base -t $tag
  if [ "x${push}" == "xtrue" ]
  then
    echo_push $tag
    docker push $tag
  fi
  for c in {gcc,clang}-*
  do
      tag=${tag_px}build-$c
      echo_build $tag
      docker build ${quiet} ${cache_args} $c -t $tag
      if [ "x${push}" == "xtrue" ]
      then
          echo_push $tag
          docker push $tag
      fi
  done
fi

if [ "x${debos}" == "xtrue" ]
then
  tag=${tag_px}debos
  echo_build $tag
  docker build ${quiet} ${cache_args} debos -t $tag
  if [ "x${push}" == "xtrue" ]
  then
    echo_push $tag
    docker push $tag
  fi
fi

if [ "x${buildroot}" == "xtrue" ]
then
  tag=${tag_px}buildroot
  echo_build $tag
  docker build ${quiet} ${cache_args} debos -t $tag
  if [ "x${push}" == "xtrue" ]
  then
    echo_push $tag
    docker push $tag
  fi
fi

if [ "x${dt_validation}" == "xtrue" ]
then
  tag=${tag_px}dt-validation
  echo_build $tag
  docker build ${quiet} ${cache_args} dt-validation -t $tag
  if [ "x${push}" == "xtrue" ]
  then
    echo_push $tag
    docker push $tag
  fi
fi

if [ "x${k8s}" == "xtrue" ]
then
  tag=${tag_px}build-k8s
  echo_build $tag
  docker build ${quiet} ${cache_args} build-k8s -t $tag
  if [ "x${push}" == "xtrue" ]
  then
    echo_push $tag
    docker push $tag
  fi
fi

if [ "x${qemu}" == "xtrue" ]
then
  tag=${tag_px}qemu
  echo_build $tag
  docker build ${quiet} ${cache_args} qemu -t $tag
  if [ "x${push}" == "xtrue" ]
  then
    echo_push $tag
    docker push $tag
  fi
fi
