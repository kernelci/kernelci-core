#!/bin/bash

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

KVER=min

# update-initramfs uses kernel config to decide how to compress ramdisk
echo "CONFIG_RD_GZIP=y" > /boot/config-$KVER

update-initramfs -c -k $KVER
