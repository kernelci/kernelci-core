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

## CA trust in root filesystems

Every Debian recipe installs the distribution's CA security update before
HTTPS downloads, then restores it after testsuite scripts have removed build
dependencies. The recipe verifies the bundle and individual certificate anchors
before producing the full tar/cpio/ext4 images and again after stripping and
crushing. The NFS initramfs also receives the updated CA bundle.

Buildroot builds verify both the target and host SDK trust stores before copying
artifacts into the publication directory. The configured `kernelci/2026.05`
branch must include the fixed `ca-certificates` package and select both
`BR2_PACKAGE_CA_CERTIFICATES` and `BR2_PACKAGE_HOST_CA_CERTIFICATES`. Otherwise
the build stops rather than publishing an image without verified CAs.

The verifier rejects the compromised eMudhra keys and their signing roots by
SHA-256 of SubjectPublicKeyInfo. This also covers cross-signed certificates. It
checks individual PEM/CRT files and hashed CApath entries, resolves absolute
symlinks inside the rootfs, and rejects missing or broken stores.

Existing dated images do not change when these recipes merge. Rebuild all
configured variants with the updated Buildroot branch and builder images, publish
under a new version, then update the runtime URLs in `kernelci-pipeline`. Include
separate references in `config/rootfs.yaml`, `config/jobs-pull-labs.yaml` and
`config/platforms-cip.yaml`. Keep the old URLs until the new artifacts exist;
do not merely change the date in a URL. The legacy `rootfs-images.yaml` is not
the active pipeline catalogue.

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
