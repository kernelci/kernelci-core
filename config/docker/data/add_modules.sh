#!/bin/sh
# In case you experience any problems with guestfish,
# you can enable extended debug:
#export LIBGUESTFS_DEBUG=1 LIBGUESTFS_TRACE=1
guestfish <<_EOF_
add chromiumos_test_image.bin
run
mount /dev/sda3 /
tar-in modules.tar /
umount-all
_EOF_
