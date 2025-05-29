#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2025 Collabora, Vignesh Raman <vignesh.raman@collabora.com>
#
# Based on the build-deqp-runner.sh script from the mesa project:
# https://gitlab.freedesktop.org/mesa/mesa/-/blob/main/.gitlab-ci/container/build-deqp-runner.sh
#
# shellcheck disable=SC2086 # we want word splitting

set -uex

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="\
    build-essential \
    ca-certificates \
    curl \
    git
"

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install --no-install-recommends -y ${BUILD_DEPS}

# Install rust
curl https://sh.rustup.rs -sSf | sh -s -- -y
. "$HOME/.cargo/env" || true

rustup component add clippy rustfmt

DEQP_RUNNER_GIT_URL="${DEQP_RUNNER_GIT_URL:-https://gitlab.freedesktop.org/mesa/deqp-runner.git}"
DEQP_RUNNER_GIT_TAG="${DEQP_RUNNER_GIT_TAG:-v0.20.0}"

git clone $DEQP_RUNNER_GIT_URL --single-branch --no-checkout
pushd deqp-runner
git checkout $DEQP_RUNNER_GIT_TAG

cargo install --locked  \
    -j ${FDO_CI_CONCURRENT:-4} \
    --root /usr/local \
    ${EXTRA_CARGO_ARGS:-} \
    --path .

popd
rm -rf deqp-runner

# Cleanup cargo cache
rm -rf /root/.cargo/registry
rustup self uninstall -y

apt-get remove --purge -y ${BUILD_DEPS}
apt-get autoremove --purge -y
apt-get clean
