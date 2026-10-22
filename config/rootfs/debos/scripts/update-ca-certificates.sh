#!/bin/sh
set -eu

suite=$1
case "$suite" in
    bookworm) minimum=20250419~deb12u2 ;;
    trixie) minimum=20250419+deb13u1 ;;
    forky|sid) minimum=20260816+nmu1 ;;
    *) echo "No verified CA security update for Debian $suite" >&2; exit 1 ;;
esac

case "$suite" in
    bookworm|trixie)
        printf 'deb http://security.debian.org/debian-security %s-security main\n' \
            "$suite" > /etc/apt/sources.list.d/kernelci-security.list
        ;;
esac

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ca-certificates
dpkg --compare-versions "$(dpkg-query -W -f='${Version}' ca-certificates)" ge "$minimum"
update-ca-certificates --fresh
