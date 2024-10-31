#!/bin/sh

set -e

# the fluster test artifacts are rather big (3-400-ish mb currently) so we can't
# put them under git, nor can we download them via gstorage buckets in SRC_URI
# because there are many files. The easiest thing to do is to pack them here and
# make them available for the ebuild.
# only do it once because it can increase build times.

printf "Downloading fluster artifacts... "
FILESDIR="${PWD}/src/third_party/chromiumos-overlay/media-libs/fluster/files"
[ ! -f ${FILESDIR}/resources.tar.xz ] &&
    "${FILESDIR}"/create-fluster-res-archive.sh  "${FILESDIR}"
echo "done"
