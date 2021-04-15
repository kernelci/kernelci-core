---
title: "kci_build"
date: 2021-02-10T11:48:13Z
draft: true
description: "Command line tool to build the Linux kernel"
---

The
[`kci_build`](https://github.com/kernelci/kernelci-core/blob/master/kci_build)
tool is used to run all the KernelCI steps related to building kernels with
extras: getting the source, creating the config file, building the binaries,
generating meta-data files and pushing the binaries to a storage server.  The
[`build-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/master/build-configs.yaml)
file contains the definitions of which kernel branches should be built and with
which combinations of compilers, architectures, kernel configurations.

The `kci_build` command is self-contained and does not require to access any
KernelCI services.  If a `kernelci-backend` instance is available, build
binaries and meta-data can be sent to it to share them.  This is however not
strictly required to build kernels and run tests using binaries stored locally,
such as in an individual developer environment.

## Example: build linux-next

The example below shows how to build a kernel from
[`linux-next`](https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git)
which is the `next` build configuration in [`build-configs.yaml`](https://github.com/kernelci/kernelci-core/config/core/build-configs.yaml).

### 1. Local settings file

In order to simplify the command line syntax and avoid passing the same options
many times, a local [settings file](../settings) can be used.  Here's a sample
one to use with this example:

```ini
[DEFAULT]
verbose: true

[kci_build]
kdir: linux
output: linux/build-x86
build_env: gcc-8
arch: x86_64
install: true
```

These settings can be stored in a `kernelci.conf` file in the current
directory.

While it's technically possible to also define `build_config: next` in the
settings file, it's clearer in this example to pass it on the command lines to
show where it is required.  For example, another branch could be built with the
same settings file and a different `--build-config` value.

Likewise, `mirror: linux-mirror.git` could be defined in the settings file.  In
this example, the mirror is optional so it's left out.  It may be more
practical to define it in a settings file for a real use-case.

Generally speaking, it's up to the user to decide which values to define in the
settings file.  They will act as defaults for all their matching command line
arguments.  See the [settings](../settings) section for more details on how
this works.


### 2. Optional: set up a local mirror

Setting up a Git mirror helps if you need to have multiple copies of the source
code checked out in different places.

To create or update an existing mirror and fetch the git history for the `next`
build configuration:

```
./kci_build update_mirror --build-config=next --mirror=linux-mirror.git
```


### 3. Create or update a local check-out

Before building a kernel, the source code needs to be available locally.  This
is typically done using Git but not exclusively, extracting a tarball archive
will also work.  To create or update an existing local Git repo, in this
example with the `--mirror` optional argument:

```
./kci_build update_repo --build-config=next --mirror=linux-mirror.git
```

Optionally, to generate additional config fragments to then be able to build
`defconfig+kselftest` or other KernelCI specific configurations:

```
./kci_build generate_fragments --build-config=next
```

### 4. Build the kernel

Once the source tree has been initialised, the kernel can be built with the
various `kci_build make_*` commands to perform each separate build step.  The
main difference between doing this with `kci_build` and manually calling
`make`, is that `kci_build` will also generate some meta-data that can be send
to the backend API and used when generating tests.  The example below uses the
[settings file](#1-local-settings-file) with the build configuration and
defconfig passed as command line arguments.

First, `init_bmeta` will create the basic build meta-data with the CPU
architecture, the compiler type, the build configuration and the kernel
revision:

```
./kci_build init_bmeta --build-config=next
```

Now it's time to actually build the kernel.  Any locally installed compiler can
be used, and there are also Docker images provided by KernelCI.  These are used
with all the kernels on kernelci.org so they help with reproducing the same
builds.  To use Docker with this example, first run these commands:

```
$ docker run -it -v $PWD:/root/kernelci-core kernelci/build-gcc-8_x86 /bin/bash
# cd /root/kernelci-core
```

Then to generate the kernel configuration, build the main image and the
modules:

```
./kci_build make_config --defconfig=defconfig
./kci_build make_kernel
./kci_build make_modules
```

All the build artifacts can be found in the specified output directory
i.e. `linux/build-x86`.  The `install: true` option means that all the files
that are suitable to be pushed to a KernelCI storage server will be installed
in the `linux/build-x86/_install_` directory.  When using kernel builds only
locally without a KernelCI backend, the `install` option can be ignored.

Note: the `build_env` option is only used to know the name and short version of
the compiler (e.g. `gcc`) and populate the meta-data for the KernelCI database.
It is not downloading a build environment or any particular toolchain version.
A future improvement would be to enable an automatic mapping between build
environment names and Docker image names; this currently has to be manually
kept in sync.


### 5. Optional: push and publish the kernel build

If you have a `kernelci-backend` instance running, you can send the kernel
binaries and the meta-data to it.  It may then be used to show results on a web
frontend, send email reports or retrieved later.

The backend is a type of database, so the `--db-config`, `--db-token` and
`--api` parameters are needed.  Passing those on the command line is far from
ideal, especially for a secret API token.  So they can be added to the settings
file as well:

```ini
[DEFAULT]
db_config: localhost

[db:localhost]
db_token: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
api: http://192.168.122.1:5001
```

With all those things defined in the settings file, pushing the kernel binaries
can be done with the following command:

```
./kci_build push_kernel
```

Then sending the build meta-data to the database can be done in a similar way
using `kci_data`:

```
./kci_data submit_build
```
