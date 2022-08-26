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

KVER=min

# update-initramfs uses kernel config to decide how to compress ramdisk
echo "CONFIG_RD_GZIP=y" > /boot/config-$KVER

update-initramfs -c -k $KVER
