#!/bin/bash
set -euo pipefail

TEST_GROUP="${1:-}"
TEST_DEV="${2:-}"

if [ -z "$TEST_GROUP" ] || [ -z "$TEST_DEV" ]; then
    echo "Usage: $0 <TEST_GROUP> <TEST_DEV>"
    exit 1
fi

LOOPBACK_REQUIRED=false
LOOPDEV=""
LOOPFILE=""

if [[ "$TEST_DEV" =~ ^/dev/loop[0-9]+$ ]]; then
    LOOPBACK_REQUIRED=true
fi

cleanup() {
    if [ "$LOOPBACK_REQUIRED" = true ] && [ -n "$LOOPDEV" ]; then
        losetup -d "$LOOPDEV" || true
        rm -f "$LOOPFILE"
    fi
}
trap cleanup EXIT

# Remove this after kernel-ci switches to upstream blktests
BLKTESTS_URL="https://github.com/linux-blktests/blktests.git"
BLKTESTS_SHA=8c610b5b
git clone -b ${BLKTESTS_SHA} ${BLKTESTS_URL}
cd blktests

if [ "$LOOPBACK_REQUIRED" = true ]; then
    LOOPFILE=$(mktemp /tmp/loopdisk.XXXX.img)
    truncate -s 1G "$LOOPFILE"
    LOOPDEV=$(losetup -f --show "$LOOPFILE")
    echo "Created loop device: $LOOPDEV"
    TEST_DEV="$LOOPDEV"
fi

echo "TEST_DEVS=('$TEST_DEV')" > config

mkdir -p /tmp/blktests-results
./check -c config "$TEST_GROUP" --output /tmp/blktests-results
