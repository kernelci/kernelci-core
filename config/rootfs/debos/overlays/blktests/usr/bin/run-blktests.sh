#!/bin/bash
set -eux

TEST_GROUP="${1:-}"
TEST_DEV="${2:-}"

if [ -z "$TEST_GROUP" ] || [ -z "$TEST_DEV" ]; then
    echo "Usage: $0 <TEST_GROUP> <TEST_DEV|loop>"
    exit 1
fi

RESULT_DIR="/tmp/blktests-results"
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

parse_results() {
    if [ -d "$RESULT_DIR" ]; then
        find "$RESULT_DIR" -type f -regex '.*/[^/]+/[^/]+/[0-9][0-9][0-9]' | sort | while read -r result_file; do
            test_name=$(basename "$result_file")
            group=$(basename "$(dirname "$result_file")")
            status=$(grep -m1 "^status" "$result_file" | cut -f2)

            case "$status" in
                pass|fail) ;;
                "not run") status="skip" ;;
                *) status="fail" ;;
            esac

            lava-test-case "${group}/${test_name}" --result "$status"
        done
    fi
}

if [ "$LOOPBACK_REQUIRED" = true ]; then
    LOOPFILE=$(mktemp /tmp/loopdisk.XXXX.img)
    truncate -s 1G "$LOOPFILE"
    LOOPDEV=$(losetup -f --show "$LOOPFILE")
    echo "Created loop device: $LOOPDEV"

    mkfs.ext4 -F "$LOOPDEV" > /dev/null
    TEST_DEV="$LOOPDEV"
fi

mkdir -p "$RESULT_DIR"
cd /usr/local/blktests/
echo "TEST_DEVS=('$TEST_DEV')" > config
set +e
./check -c config "$TEST_GROUP" --output "$RESULT_DIR"
set -e
exit_code=$?

set +x
parse_results
set -x

exit $exit_code
