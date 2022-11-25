#!/bin/bash

patch -p1 << EOF
diff --git a/usr/share/initramfs-tools/scripts/local.dist b/usr/share/initramfs-tools/scripts/local
index 4ec926c..ca06c0b 100644
--- a/usr/share/initramfs-tools/scripts/local.dist
+++ b/usr/share/initramfs-tools/scripts/local
@@ -60,6 +60,12 @@ local_device_setup()
 	local time_elapsed
 	local count
 
+	expr match ${dev_id#/dev/} "ram" > /dev/null
+	if [ $? = 0 ]; then
+		echo "Ignoring ${dev_id}.  We're already in a ramdisk."
+		return 1
+	fi
+
 	wait_for_udev 10
 
 	# Load ubi with the correct MTD partition and return since fstype
EOF

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
