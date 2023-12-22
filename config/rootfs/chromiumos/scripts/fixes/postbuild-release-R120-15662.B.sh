#!/bin/bash
#
#
#As described in b/295364868 if this flag is enabled in mke2fs,
#and we test in KernelCI newest kernel (post-5.15), it will convert fs 
#using this flag and then when we load pre-5.15,
#on old kernel, it will not be able to mount filesystem,
#and as result initiate self_repair with wipe of stateful partition.
#
# We can remove this workaround when all DUT dont have kernel older than 5.15
echo "Removing orphan_file from mke2fs.conf (R114, R116)"
cd "${DATA_DIR}/${BOARD}"
# This is guestfish commands, even they are similar to bash, it is not shell
# rm-rf is for example guestfish specific command
sudo guestfish <<_EOF_
add chromiumos_test_image.bin
run
mount /dev/sda3 /
download /etc/mke2fs.conf mke2fs.conf
_EOF_


# remove ",orphan_file" from mke2fs.conf
sudo sed -i 's/,orphan_file//' mke2fs.conf

# upload modified mke2fs.conf back
sudo guestfish <<_EOF_
add chromiumos_test_image.bin
run
mount /dev/sda3 /
upload mke2fs.conf /etc/mke2fs.conf
_EOF_

cd -
