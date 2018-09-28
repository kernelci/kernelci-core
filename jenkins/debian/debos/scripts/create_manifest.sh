#!/bin/bash

set -e

# Create a manifest in JSON with the build data

MANIFEST="/scratch/root/build_info.json"
BUILDFILE="/scratch/root/build_info.txt"

echo '{' >> $MANIFEST
echo '  "date":' \"`date -u`\" ',' >> $MANIFEST
echo '  "distro": "debian",' >> $MANIFEST
echo '  "distro_version":' \"`cat /scratch/root/etc/debian_version`\" ',' >> $MANIFEST
cat $BUILDFILE >> $MANIFEST
echo '}' >> $MANIFEST
