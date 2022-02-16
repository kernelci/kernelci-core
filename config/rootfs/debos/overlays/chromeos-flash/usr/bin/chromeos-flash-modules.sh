#!/bin/bash

set -xe

mount_special_fs()
{
    local base="${1:-/root/chromeos}"

    mount udev -t devtmpfs "$base"/dev
    mount proc -t proc "$base"/proc
    mount sysfs -t sysfs "$base"/sys
    mount -t tmpfs tmpfs "$base"/tmp
    mount
}

umount_special_fs()
{
    local base="${1:-/root/chromeos}"

    umount "$base"/dev
    umount "$base"/proc
    umount "$base"/sys
    umount "$base"/tmp
    mount
}

flash_chromeos()
{
    local dev
    local mount_dir=$(basename "$IMAGE_MOUNTPOINT")
    local root_path=$(dirname "$IMAGE_MOUNTPOINT")

    echo "Setting up Chrome OS chroot..."
    mkdir -p "$IMAGE_MOUNTPOINT"
    cd "$root_path"
    dev=$(losetup -P -f --show "$IMAGE_NAME")
    mount "$dev"p3 "$mount_dir" -o ro
    mount_special_fs "$IMAGE_MOUNTPOINT"
    mount --bind . "$mount_dir"/mnt/empty
    ls -l "$mount_dir"/mnt/empty/"$IMAGE_NAME"
    ls -l "$mount_dir"/dev/mmc*

    echo "Starting to flash..."
    chroot "$mount_dir" \
         /usr/sbin/chromeos-install \
        --dst /dev/mmcblk0 \
        --payload_image /mnt/empty/"$IMAGE_NAME" \
        --yes
    sync

    umount_special_fs "$IMAGE_MOUNTPOINT"
    umount "$mount_dir"/mnt/empty
    umount "$mount_dir"
    losetup -d "$dev"
}

enable_rw()
{
    local mount_dir=$(basename "$IMAGE_MOUNTPOINT")
    local root_path=$(dirname "$IMAGE_MOUNTPOINT")

    echo "Making the rootfs writeable..."
    mkdir -p "$IMAGE_MOUNTPOINT"
    cd "$root_path"
    mount /dev/mmcblk0p3 "$mount_dir" -o ro
    mount_special_fs "$IMAGE_MOUNTPOINT"
    cd "$mount_dir"
    chroot . \
        /usr/share/vboot/bin/make_dev_ssd.sh \
        --remove_rootfs_verification \
        --force
    cd "$root_path"
    umount_special_fs "$IMAGE_MOUNTPOINT"
    umount "$mount_dir"
    sync
    partprobe /dev/mmcblk0
}

fixup_tmpfiles()
{
    local mount_dir=$(basename "$IMAGE_MOUNTPOINT")
    local root_path=$(dirname "$IMAGE_MOUNTPOINT")

    echo "Fixing up tmpfiles..."
    mkdir -p "$IMAGE_MOUNTPOINT"
    cd "$root_path"
    mount /dev/mmcblk0p3 "$mount_dir"
    mount_special_fs "$IMAGE_MOUNTPOINT"
    cd "$mount_dir"
    mount /dev/mmcblk0p1 mnt/stateful_partition
    chroot . chown root: .
    ls -l mnt/stateful_partition
    chroot . \
        /bin/systemd-tmpfiles \
        --create --remove --boot --prefix /mnt/stateful_partition
    chroot . ls -la .
    ls -l mnt/stateful_partition
    umount mnt/stateful_partition
    cd "$root_path"
    umount_special_fs "$IMAGE_MOUNTPOINT"
    umount "$mount_dir"
    sync
}

install_modules()
{
    local mount_dir=$(basename "$IMAGE_MOUNTPOINT")
    local root_path=$(dirname "$IMAGE_MOUNTPOINT")
    local modules_tarball=$(basename "$MODULES_URL")

    echo "Downloading modules from $MODULES_URL..."
    mkdir -p "$IMAGE_MOUNTPOINT"
    cd "$root_path"
    wget --no-check-certificate "$MODULES_URL"
    mount /dev/mmcblk0p3 "$mount_dir"

    echo "Installing modules..."
    cd "$mount_dir"
    ls -l lib/modules
    rm -rf lib/modules
    tar xzf "$root_path/$modules_tarball"
    chown root: -R lib
    ls -l lib/modules
    cd "$root_path"
    umount "$mount_dir"
    sync
}

commands="${*:-flash_chromeos enable_rw fixup_tmpfiles install_modules}"
IMAGE_NAME="${IMAGE_NAME:-octopus-chromiumos-test-image.bin}"
IMAGE_MOUNTPOINT="${IMAGE_MOUNTPOINT:-/root/chromeos}"
MODULES_URL="${MODULES_URL:-http://images.collabora.com/lava/chromeos/modules-4.14.243.tar.gz}"

for cmd in $commands; do
    echo "Running [$cmd]"
    $cmd
done

exit 0
