#!/bin/bash

set -x

tree_name=${TREE_NAME}
echo "Creating defconfigs ${TREE} (${TREE_NAME}/${BRANCH}/${GIT_DESCRIBE}) for arch ${ARCH}"


wget -q $SRC_TARBALL && tar -zxf linux-src.tar.gz


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

# defconfigs + fragments
if [ ${ARCH} = "arm" ]; then
  ### DEFCONFIG_LIST+="allmodconfig "
  DEFCONFIG_LIST+="multi_v7_defconfig+CONFIG_ARM_LPAE=y "
  DEFCONFIG_LIST+="multi_v7_defconfig+CONFIG_CPU_BIG_ENDIAN=y "
  DEFCONFIG_LIST+="multi_v7_defconfig+CONFIG_PROVE_LOCKING=y "
  DEFCONFIG_LIST+="versatile_defconfig+CONFIG_OF_UNITTEST=y "
  DEFCONFIG_LIST+="multi_v7_defconfig+CONFIG_THUMB2_KERNEL=y+CONFIG_ARM_MODULE_PLTS=y "
  DEFCONFIG_LIST+="multi_v7_defconfig+CONFIG_SMP=n "
  DEFCONFIG_LIST+="multi_v7_defconfig+CONFIG_EFI=y "
  DEFCONFIG_LIST+="multi_v7_defconfig+CONFIG_EFI=y+CONFIG_ARM_LPAE=y "

  # Platform specific
  if [ -e arch/${ARCH}/configs/mvebu_v7_defconfig ]; then
    DEFCONFIG_LIST+="mvebu_v7_defconfig+CONFIG_CPU_BIG_ENDIAN=y "
  fi
  
  # tree specific
  if [ ${tree_name} = "next" ]; then
    DEFCONFIG_LIST+="allmodconfig "
  fi
fi

if [ ${ARCH} = "arm64" ]; then
  DEFCONFIG_LIST+="defconfig+CONFIG_CPU_BIG_ENDIAN=y "
  DEFCONFIG_LIST+="defconfig+CONFIG_OF_UNITTEST=y "
  DEFCONFIG_LIST+="defconfig+CONFIG_RANDOMIZE_BASE=y "
  # ACPI currently depends on EXPERT on arm64
  DEFCONFIG_LIST+="defconfig+CONFIG_EXPERT=y+CONFIG_ACPI=y "
  DEFCONFIG_LIST+="allmodconfig "

  # Enable KASAN for non-stable until image size issues are sorted out
  if [ ${tree_name} != "stable" ] && [ ${tree_name} != "stable-rc" ]; then
    DEFCONFIG_LIST+="defconfig+CONFIG_KASAN=y "
  fi
fi

if [ ${ARCH} = "x86" ]; then
  DEFCONFIG_LIST+="defconfig+CONFIG_OF_UNITTEST=y "
  DEFCONFIG_LIST+="defconfig+CONFIG_KASAN=y "
  DEFCONFIG_LIST+="allmodconfig "
  DEFCONFIG_LIST+="allmodconfig+CONFIG_OF=n "
  DEFCONFIG_LIST+="i386_defconfig "

  # Fragments
  FRAGS="arch/x86/configs/kvm_guest.config"
  for frag in ${FRAGS}; do
    if [ -e $frag ]; then
      DEFCONFIG_LIST+="defconfig+$frag "
    fi
  done
fi

# kselftests
KSELFTEST_FRAG=kernel/configs/kselftest.config
if [ -e $KSELFTEST_FRAG ]; then
  DEFCONFIG_LIST+="$base_defconfig+$KSELFTEST_FRAG "
fi

# Tree specific fragments: stable
if [ ${tree_name} = "stable" ] || [ ${tree_name} = "stable-rc" ]; then
  # Don't do allmodconfig builds
  DEFCONFIG_LIST=${DEFCONFIG_LIST/allmodconfig/}
fi

# Security testing features
DEFCONFIG_LIST+="$base_defconfig+CONFIG_LKDTM=y "

# Tree specific fragments: LSK + KVM fragments
if [ ${tree_name} = "lsk" ] || [ ${tree_name} = "anders" ]; then
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


cat << EOF > ${WORKSPACE}/${TREE_NAME}_${BRANCH}_${ARCH}-build.properties
ARCH=$ARCH
DEFCONFIG_LIST=$DEFCONFIG_LIST
TREE=${TREE}
SRC_TARBALL=$SRC_TARBALL
TREE_NAME=$tree_name
BRANCH=${BRANCH}
GIT_DESCRIBE=${GIT_DESCRIBE}
GIT_DESCRIBE_VERBOSE=${GIT_DESCRIBE_VERBOSE}
COMMIT_ID=${COMMIT_ID}
PUBLISH=true
EOF

cat ${WORKSPACE}/${TREE_NAME}_${BRANCH}_${ARCH}-build.properties