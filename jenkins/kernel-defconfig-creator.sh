#!/bin/bash

set -x
export PATH=${WORKSPACE}/kernelci-build:${PATH}

echo "Creating defconfigs ${TREE} (${TREE_NAME}/${BRANCH}/${GIT_DESCRIBE}) for arch ${ARCH}"

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

if [ ! -d arch/${ARCH}/configs ]
then
    echo "No configs directory for arch ${ARCH}"
    exit 2
fi

# debug
ls arch/${ARCH}/configs

# defconfigs
DEFCONFIG_LIST="allnoconfig "
DEFCONFIG_LIST+=`(cd arch/${ARCH}/configs; echo *defconfig)`
DEFCONFIG_LIST+=" "

base_defconfig="defconfig"
if [ ${ARCH} = "arm" ]; then
  base_defconfig="multi_v7_defconfig"
fi

# tinyconfig
if [ -e kernel/configs/tiny.config ]; then
  DEFCONFIG_LIST+="tinyconfig "
fi

# minimal set of in-tree defconfigs
DEFCONFIG_STABLE=$DEFCONFIG_LIST

# defconfigs + fragments
if [ ${ARCH} = "arm" ]; then
  ### DEFCONFIG_LIST+="allmodconfig "
  DEFCONFIG_LIST+="multi_v7_defconfig+CONFIG_CPU_BIG_ENDIAN=y "
  DEFCONFIG_LIST+="multi_v7_defconfig+CONFIG_SMP=n "
  DEFCONFIG_LIST+="multi_v7_defconfig+CONFIG_EFI=y+CONFIG_ARM_LPAE=y "

  # Platform specific
  if [ -e arch/${ARCH}/configs/mvebu_v7_defconfig ]; then
    DEFCONFIG_LIST+="mvebu_v7_defconfig+CONFIG_CPU_BIG_ENDIAN=y "
  fi
  
  # tree specific
  if [ ${TREE_NAME} = "next" ]; then
    DEFCONFIG_LIST+="allmodconfig "
  fi

  # Ard specific tree and branch defconfigs.
  if [ ${TREE_NAME} = "ardb" ] && [ ${BRANCH} = "arm-kaslr-latest" ]; then
    DEFCONFIG_LIST+="multi_v7_defconfig+CONFIG_RANDOMIZE_BASE=y "
    DEFCONFIG_LIST+="multi_v7_defconfig+CONFIG_THUMB2_KERNEL=y+CONFIG_RANDOMIZE_BASE=y "
    DEFCONFIG_LIST+="multi_v5_defconfig "
    DEFCONFIG_LIST+="omap2plus_defconfig+CONFIG_RANDOMIZE_BASE=y "
    DEFCONFIG_LIST+="omap2plus_defconfig "
  fi
fi

if [ ${ARCH} = "arm64" ]; then
  DEFCONFIG_LIST+="defconfig+CONFIG_CPU_BIG_ENDIAN=y "
  DEFCONFIG_LIST+="defconfig+CONFIG_RANDOMIZE_BASE=y "
  DEFCONFIG_LIST+="allmodconfig "
fi

if [ ${ARCH} = "x86" ]; then
  DEFCONFIG_LIST+="allmodconfig "

  # Fragments
  FRAGS="arch/x86/configs/kvm_guest.config"
  for frag in ${FRAGS}; do
    if [ -e $frag ]; then
      DEFCONFIG_LIST+="defconfig+$frag "
    fi
  done
fi

# debug builds
DEBUG_FRAG=kernel/configs/debug.config
if [ -e $DEBUG_FRAG ]; then
  DEFCONFIG_LIST+="$base_defconfig+$DEBUG_FRAG "
fi

# kselftests
KSELFTEST_FRAG=kernel/configs/kselftest.config
if [ -e $KSELFTEST_FRAG ]; then
  DEFCONFIG_LIST+="$base_defconfig+$KSELFTEST_FRAG "
fi

# Tree specific fragments: stable
if [ ${TREE_NAME} = "stable" ] || [ ${TREE_NAME} = "stable-rc" ]; then
  # only do minimal "known stable" defconfigs
  DEFCONFIG_LIST=$DEFCONFIG_STABLE
fi

# Tree specific fragments: LSK + KVM fragments
if [ ${TREE_NAME} = "lsk" ] || [ ${TREE_NAME} = "anders" ]; then
  FRAGS="linaro/configs/kvm-guest.conf"

  # For -rt kernels, build with RT fragment
  RT_FRAG=kernel/configs/preempt-rt.config
  if [ ! -f ${RT_FRAG} ]; then
    RT_FRAG=linaro/configs/preempt-rt.conf
  fi

  grep -q "config PREEMPT_RT_FULL" kernel/Kconfig.preempt
  if [ $? = 0 ]; then
     FRAGS+=" $RT_FRAG "
  fi

  for frag in ${FRAGS}; do
    if [ -e $frag ]; then
      DEFCONFIG_LIST+="$base_defconfig+$frag "
    fi
  done

  # KVM host: only enable for LPAE-enabled kernels
  KVM_HOST_FRAG=linaro/configs/kvm-host.conf
  if [ -e $KVM_HOST_FRAG ]; then
    lpae_base="multi_v7_defconfig+CONFIG_ARM_LPAE=y"
    if [[ $DEFCONFIG_LIST == *"${lpae_base}"* ]]; then
        DEFCONFIG_LIST+="${lpae_base}+$KVM_HOST_FRAG "
    fi
  fi

  # Linaro base + distro frags
  if [ -e linaro/configs/linaro-base.conf -a -e linaro/configs/distribution.conf ]; then
      DEFCONFIG_LIST+="$base_defconfig+linaro/configs/linaro-base.conf+linaro/configs/distribution.conf "
  fi

  # Android/AOSP fragments: combined together
  if [ -e android/configs ]; then
    FRAG_A=""
    FRAGS="android/configs/android-base.cfg android/configs/android-recommended.cfg"
    for frag in ${FRAGS}; do
      if [ -e $frag ]; then
        FRAG_A+="+$frag"
      fi
    done
    if [ -n "$FRAG_A" ]; then
      DEFCONFIG_LIST+=" $base_defconfig$FRAG_A "
      # Also build vexpress_defconfig + Android for testing on QEMU
      if [ ${ARCH} = "arm" ]; then
        DEFCONFIG_LIST+=" vexpress_defconfig$FRAG_A "
      fi
    fi
  fi
fi

DEFCONFIG_ARRAY=( $DEFCONFIG_LIST )
DEFCONFIG_COUNT=${#DEFCONFIG_ARRAY[@]}
echo $DEFCONFIG_COUNT > ${ARCH}_defconfig.count
push-source.py --tree ${TREE_NAME} --branch ${BRANCH} --describe ${GIT_DESCRIBE} --api ${API} --token ${API_TOKEN} --file ${ARCH}_defconfig.count

cat << EOF > ${WORKSPACE}/${TREE_NAME}_${BRANCH}_${ARCH}-build.properties
ARCH=$ARCH
DEFCONFIG_LIST=$DEFCONFIG_LIST
TREE=${TREE}
SRC_TARBALL=$SRC_TARBALL
TREE_NAME=$TREE_NAME
BRANCH=${BRANCH}
GIT_DESCRIBE=${GIT_DESCRIBE}
GIT_DESCRIBE_VERBOSE=${GIT_DESCRIBE_VERBOSE}
COMMIT_ID=${COMMIT_ID}
PUBLISH=true
EOF

cat ${WORKSPACE}/${TREE_NAME}_${BRANCH}_${ARCH}-build.properties
