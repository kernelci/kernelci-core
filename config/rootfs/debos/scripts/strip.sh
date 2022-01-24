#!/bin/sh

# Strip the image to a small minimal system without removing the debian
# toolchain.

set -e

# Copy timezone file and remove tzdata package
rm -rf /etc/localtime
cp /usr/share/zoneinfo/Etc/UTC /etc/localtime

EXTRA_PACKAGES=$(echo "${1}" | xargs -n1)
EXTRA_TEMP_FILE=`mktemp strip_extra_packages.XXXXXX`
exec 3>"$EXTRA_TEMP_FILE"
echo "$EXTRA_PACKAGES" | sort | uniq >&3

UNNEEDED_PACKAGES=" libfdisk1 \
tzdata"
UNNEEDED_TEMP_FILE=$(mktemp strip_unneeded_packages.XXXXXX)
exec 4>"$UNNEEDED_TEMP_FILE"
echo "$UNNEEDED_PACKAGES" | xargs -n1 | sort | uniq >&4

PACKAGES_TO_REMOVE=$(comm  -23  "$UNNEEDED_TEMP_FILE" "$EXTRA_TEMP_FILE")

export DEBIAN_FRONTEND=noninteractive

exec 3>&-
exec 4>&-

# Removing unused packages
for PACKAGE in ${PACKAGES_TO_REMOVE}
do
	echo ${PACKAGE}
	if ! apt-get remove --purge --yes "${PACKAGE}"
	then
		echo "WARNING: ${PACKAGE} isn't installed"
	fi
done

apt-get autoremove --yes || true

# Dropping logs
rm -rf /var/log/*

# Dropping documentation, localization, i18n files, etc
rm -rf /usr/share/doc/*
rm -rf /usr/share/locale/*
rm -rf /usr/share/man
rm -rf /usr/share/i18n/*
rm -rf /usr/share/info/*
rm -rf /usr/share/lintian/*
rm -rf /usr/share/common-licenses/*
rm -rf /usr/share/mime/*

# Dropping reportbug scripts
rm -rf /usr/share/bug

# Drop udev hwdb not required on a stripped system
rm -rf /lib/udev/hwdb.bin /lib/udev/hwdb.d/*

# Drop all gconv conversions && binaries
rm -rf usr/bin/iconv
rm -rf usr/sbin/iconvconfig
rm -rf usr/lib/*/gconv/

# Remove libusb database
rm -rf usr/sbin/update-usbids
rm -rf var/lib/usbutils/usb.ids
rm -rf usr/share/misc/usb.ids
