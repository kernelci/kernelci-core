#!/bin/bash

set -euo pipefail

patch -p1 << 'EOF'
--- a/usr/share/initramfs-tools/scripts/nfs-premount/wait_ethernet	1970-01-01 02:00:00.000000000 +0200
+++ b/usr/share/initramfs-tools/scripts/nfs-premount/wait_ethernet	2022-11-25 12:38:46.037498198 +0200
@@ -0,0 +1,21 @@
+#!/bin/sh
+. /scripts/functions
+
+wait_ethernet() {
+  local netdevwait=60
+  echo "Waiting up to ${netdevwait} secs for any ethernet to become available"
+  while [ "$(time_elapsed)" -lt "$netdevwait" ]; do
+    for device in /sys/class/net/* ; do
+      if [ -f "$device/type" ]; then
+        current_type=$(cat "$device/type")
+        if [ "${current_type}" = "1" ]; then
+          echo "Device ${device} found"
+          return
+        fi
+      fi
+    done
+    sleep 1
+  done
+}
+
+wait_ethernet
EOF

chmod +x /usr/share/initramfs-tools/scripts/nfs-premount/wait_ethernet

nfs_packages_before=$(mktemp)
dpkg-query -W -f='${binary:Package}\t${db:Status-Status}\n' \
  | sed -n 's/\tinstalled$//p' \
  | sort -u > "$nfs_packages_before"

# mount.nfs only needs libtirpc and its shared-library dependencies.  Extract
# the helper without installing nfs-common, whose unrelated device-mapper hook
# would otherwise make the initramfs larger.
if ! dpkg-query -W -f='${db:Status-Status}' libtirpc3t64 2>/dev/null \
    | grep -qx installed; then
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libtirpc3t64
fi
nfs_package_dir=$(mktemp -d)
chown _apt:root "$nfs_package_dir"
(
  cd "$nfs_package_dir"
  apt-get download nfs-common
)
nfs_common_deb=$(find "$nfs_package_dir" -maxdepth 1 -type f \
  -name 'nfs-common_*.deb' -print -quit)
if [[ -z "$nfs_common_deb" ]]; then
  echo "Unable to download nfs-common" >&2
  exit 1
fi
dpkg-deb --extract "$nfs_common_deb" "$nfs_package_dir/root"
install -m 0755 "$nfs_package_dir/root/usr/sbin/mount.nfs" \
  /usr/lib/kernelci/mount.nfs
rm -rf -- "$nfs_package_dir"

KVER=min

# update-initramfs uses kernel config to decide how to compress ramdisk
echo "CONFIG_RD_GZIP=y" > /boot/config-$KVER

update-initramfs -c -k $KVER

# These files are only needed while constructing the initramfs.
rm -f /etc/initramfs-tools/hooks/zz-kernelci-nfs \
  /usr/lib/kernelci/nfsmount \
  /usr/lib/kernelci/mount.nfs
rmdir --ignore-fail-on-non-empty /usr/lib/kernelci

nfs_packages_after=$(mktemp)
nfs_packages_remove_file=$(mktemp)
dpkg-query -W -f='${binary:Package}\t${db:Status-Status}\n' \
  | sed -n 's/\tinstalled$//p' \
  | sort -u > "$nfs_packages_after"
comm -13 "$nfs_packages_before" "$nfs_packages_after" \
  > "$nfs_packages_remove_file"
mapfile -t nfs_packages_to_remove < "$nfs_packages_remove_file"
rm -f "$nfs_packages_before" "$nfs_packages_after" \
  "$nfs_packages_remove_file"
if ((${#nfs_packages_to_remove[@]})); then
  DEBIAN_FRONTEND=noninteractive apt-get purge -y \
    "${nfs_packages_to_remove[@]}"
fi
apt-get clean
