#!/bin/sh
set -e

# Crush into a minimal production image to be deployed via some type of image
# updating system.
# IMPORTANT: The Debian system is not longer functional at this point,
# for example, apt and dpkg will stop working

UNNEEDED_PACKAGES="apt libapt-pkg5.0 "\
"ncurses-bin ncurses-base libncursesw5 libncurses5 "\
"perl-base "\
"debconf libdebconfclient0 "\
"libfdisk1 libdevmapper1.02.1 "\
"insserv "\
"init-system-helpers "\
"cpio "\
"passwd "\
"libsemanage1 libsemanage-common "\
"libsepol1 "\
"gzip "\
"gnupg "\
"gpgv "\
"hostname "\
"adduser "\
"debian-archive-keyring "\


# Removing unneeded packages
for PACKAGE in ${UNNEEDED_PACKAGES}
do
	echo "Forcing removal of ${PACKAGE}"
	if ! dpkg --purge --force-remove-essential --force-depends "${PACKAGE}"
	then
		echo "WARNING: ${PACKAGE} isn't installed"
	fi
done

# Show what's left package-wise before dropping dpkg itself
COLUMNS=300 dpkg -l

# Drop dpkg
dpkg --purge --force-remove-essential --force-depends  dpkg

# No apt or dpkg, no need for its configuration archives
rm -rf etc/apt
rm -rf etc/dpkg

# Drop directories not part of ostree
# Note that /var needs to exist as ostree bind mounts the deployment /var over
# it
rm -rf var/* srv share

# ca-certificates are in /etc drop the source
rm -rf usr/share/ca-certificates

# No bash, no need for completions
rm -rf usr/share/bash-completion

# No zsh, no need for comletions
rm -rf usr/share/zsh/vendor-completions

# drop gcc-6 python helpers
rm -rf usr/share/gcc-6

# Drop sysvinit leftovers
rm -rf etc/init.d
rm -rf etc/rc[0-6S].d

# Drop upstart helpers
rm -rf etc/init

# Various xtables helpers
rm -rf usr/lib/xtables

# Drop all locales
# TODO: only remaining locale is actually "C". Should we really remove it?
rm -rf usr/lib/locale/*

# partition helpers
rm usr/sbin/*fdisk

# local compiler
rm usr/bin/localedef

# Systemd dns resolver
#find usr etc -name '*systemd-resolve*' -prune -exec rm -r {} \;

# Systemd network configuration
#find usr etc -name '*networkd*' -prune -exec rm -r {} \;

# systemd ntp client (connman is in use)
#find usr etc -name '*timesyncd*' -prune -exec rm -r {} \;

# systemd hw database manager (connman is in use)
find usr etc -name '*systemd-hwdb*' -prune -exec rm -r {} \;

# No need for fuse
find usr etc -name '*fuse*' -prune -exec rm -r {} \;

# lsb init function leftovers
rm -rf usr/lib/lsb

# Utils using ncurses
rm usr/bin/pg
rm usr/bin/watch
rm usr/bin/slabtop

# boot analyser
rm usr/bin/systemd-analyze

# Only needed when adding libraries
rm usr/sbin/ldconfig*

# Games, unused
rmdir usr/games

# Unused systemd generators
rm lib/systemd/system-generators/systemd-cryptsetup-generator
rm lib/systemd/system-generators/systemd-debug-generator
rm lib/systemd/system-generators/systemd-gpt-auto-generator
rm lib/systemd/system-generators/systemd-hibernate-resume-generator
rm lib/systemd/system-generators/systemd-rc-local-generator
rm lib/systemd/system-generators/systemd-system-update-generator
rm lib/systemd/system-generators/systemd-sysv-generator


# Efi blobs
rm -rf usr/lib/systemd/boot

# Translation catalogs
rm -rf usr/lib/systemd/catalog

# Misc systemd utils
rm usr/bin/bootctl
rm usr/bin/busctl
rm usr/bin/hostnamectl
rm usr/bin/localectl
rm usr/bin/systemd-cat
rm usr/bin/systemd-cgls
rm usr/bin/systemd-cgtop
rm usr/bin/systemd-delta
rm usr/bin/systemd-detect-virt
rm usr/bin/systemd-mount
rm usr/bin/systemd-path
rm usr/bin/systemd-run
rm usr/bin/systemd-socket-activate

# Remove pam module to authenticate against a DB
# plus libdb-5.3.so that is only used by this pam module
rm usr/lib/*/security/pam_userdb.so
rm usr/lib/*/libdb-5.3.so

# remove NSS support for nis, nisplus and hesiod
rm usr/lib/*/libnss_hesiod*
rm usr/lib/*/libnss_nis*
