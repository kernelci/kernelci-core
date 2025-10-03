#!/bin/bash
set -euo pipefail
set -x

TEST_GROUP="${1:-}"
TEST_DEV="${2:-}"

if [ -z "$TEST_GROUP" ] || [ -z "$TEST_DEV" ]; then
    echo "Usage: $0 <TEST_GROUP> <TEST_DEV|loop>"
    exit 1
fi

LOOPBACK_REQUIRED=false
LOOPDEV=""
LOOPFILE=""

if [ "$TEST_DEV" = "loop" ]; then
    LOOPBACK_REQUIRED=true
fi

cleanup() {
    if [ "$LOOPBACK_REQUIRED" = true ] && [ -n "${LOOPDEV:-}" ]; then
        losetup -d "$LOOPDEV" || true
    fi
    [ -n "${LOOPFILE:-}" ] && rm -f "$LOOPFILE"
}
trap cleanup EXIT

if [ "$LOOPBACK_REQUIRED" = true ]; then
    LOOPFILE=$(mktemp /tmp/loopdisk.XXXX.img)
    truncate -s 1G "$LOOPFILE"
    LOOPDEV=$(losetup -f --show "$LOOPFILE")
    echo "Created loop device: $LOOPDEV"

    mkfs.ext4 -F "$LOOPDEV" > /dev/null
    TEST_DEV="$LOOPDEV"
fi

mkdir -p /tmp/blktests-results
cd /usr/local/blktests/
echo "TEST_DEVS=('$TEST_DEV')" > config
./check -c config "$TEST_GROUP" --output /tmp/blktests-results
