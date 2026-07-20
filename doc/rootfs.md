---
title: "Root filesystem images"
date: 2026-07-21
draft: false
description: "Build KernelCI Debos and Buildroot root filesystems"
weight: 3
---

The `kci rootfs` command builds the root filesystem images used by KernelCI.
Debos and Buildroot are the supported backends.  Configuration, recipes,
scripts, and overlays are maintained together in `kernelci-core`.

## Requirements

Install the local package and ensure the current user can access Docker:

```shell
python3 -m pip install .
docker version
```

The builder does not invoke `sudo`.  Use a rootless container engine or grant
the user access to the Docker daemon before starting a build.

## Inspect and validate configurations

```shell
kci rootfs validate
kci rootfs list
kci rootfs list --type buildroot --format json
kci rootfs variants trixie
```

The default configuration is `config/core/rootfs-configs.yaml`, with recipes
and assets below `config/rootfs`.  Use `--config` and `--data-dir` to select
other locations.

## Build images

Build one architecture explicitly:

```shell
kci rootfs build trixie --arch amd64
kci rootfs build buildroot-baseline --arch x86
```

Build every architecture configured for one image:

```shell
kci rootfs build trixie --all-arches
```

Artifacts are written to `output/<configuration>/<architecture>/`.  Failed
builds do not replace the previous successful output.  Add `--keep-failed` to
retain partial staging files for debugging.

Buildroot source, output, and downloads are reused below
`.cache/kernelci/rootfs`.  Change these paths with `--output-dir` and
`--cache-dir`.

The default builder images are:

* `ghcr.io/kernelci/debos:kernelci`
* `ghcr.io/kernelci/buildroot:kernelci`

Override them with `--debos-image` or `--buildroot-image`.  Image pull policy
is controlled with `--pull always|missing|never`.  CI uses `always`; local
builds default to `missing`.

Each successful directory includes `rootfs-build.json` with the normalized
configuration, source revisions, resolved builder image identity, and SHA-256
checksums of generated files.

## GitHub workflow

The `Build rootfs images` workflow accepts one configuration and either one
architecture or `all`.  Architectures are built in parallel and published as:

```text
<configuration>/<YYYYMMDD.N>/<architecture>/
```

Publication uses protected `staging` and `production` environments.  Each
environment must define these secrets and variables:

* Secrets: `ROOTFS_HOST`, `ROOTFS_USERNAME`, `ROOTFS_SSH_KEY`, `ROOTFS_PORT`
* Variables: `ROOTFS_BASE_DIR`, `ROOTFS_PUBLIC_URL`

Configure required reviewers on the production environment before enabling
the workflow.

## Deprecated command

`kci_rootfs` is a temporary compatibility wrapper.  It forwards validation,
listing, and build operations to `kci rootfs` while retaining the historical
`_install_` output layout.  It will be removed in the next minor release.
