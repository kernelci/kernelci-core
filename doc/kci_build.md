## `kci_build`

The
[`kci_build`](https://github.com/kernelci/kernelci-core/blob/master/kci_build)
tool is used to run all the KernelCI steps related to building kernels: getting
the source, creating the config file, building the binaries, generating
meta-data files and pushing the binaries to a storage server.  The
[`build-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/master/build-configs.yaml)
file contains the definitions of which kernel source code should be built (git
branches) and how (compilers, architectures, kernel configurations).

Running `kci_build` does not require any other KernelCI components to be
installed.  If a `kernelci-backend` instance is available, build binaries and
meta-data can be sent to it to share them.  This is however not strictly
required to run tests using kernel binaries stored locally, such as in an
individual developer environment.

The example below shows how to build a kernel from
[`linux-next`](https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git)
which is called the `next` build configuration in `build-configs.yaml`:

### 1. Optional: set up a local mirror

Setting up a git mirror helps if you need to have multiple copies of the source
code checked out in different places.

To create or update an existing mirror and fetch the git history for the `next`
build configuration:

```
./kci_build update_mirror --config=next --mirror=linux-mirror.git
```

Tip: it's quicker to create a mainline mirror first if you already have a Linux
kernel git repo checked out locally, using the `--reference` option.  For
example:

```
git clone \
  --mirror git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git \
  --reference=~/src/linux \
  linux-mirror.git
```

### 2. Create a local check-out (or update an existing one)

Before building a Linux kernel revision, the source code needs to be available
locally.  This is typically done using git but any source form will work
(extracting a tarball archive...).  To create or update an existing local git
repo, with the `--mirror` optional argument:

```
./kci_build update_repo --config=next --kdir=linux --mirror=linux-mirror.git
```

Optionally, to generate additional config fragments to then be able to build
`defconfig+kselftest` or other KernelCI specific configurations:

```
./kci_build generate_fragments --config=next --kdir=linux
```

### 3. Build the kernel

Once the git repo has been initialised, or the source code is available in any
form, the kernel can be built with the `build_kernel` command.  In this
example, it's building for the `x64_64` architecture with the `defconfig` and
`gcc-8` compiler:

```
./kci_build build_kernel \
  --defconfig=defconfig --arch=x86_64 --build-env=gcc-8 --kdir=linux
```

To see the compiler output, add `--verbose`.  The output binaries can be found
in `linux/build`.

To build again without regenerating the kernel config file, just omit the
`--defconfig` argument:

```
./kci_build build_kernel \
  --arch=x86_64 --build-env=gcc-8 --kdir=linux
```

Note: the `build-env` option is only used to know the name of the compiler
(e.g. `gcc`) and populate the meta-data for the KernelCI database, it is not
downloading a build environment or any particular toolchain version.  A future
improvement would be to enable using a Docker image as with Jenkins builds
([`jenkins/build.jpl`](https://github.com/kernelci/kernelci-core/blob/master/jenkins/build.jpl)).

### 4. Install the kernel binaries in a local directory

Once the kernel has been built, the binaries can be installed in a local
directory with added meta-data in `bmeta.json` such as the list of device tree
(`.dtb`) files, the build log and several other things needed to run some tests
later on using [`kci_test`](kci_test.md).  It's also an intermediate step
before publishing a kernel build to KernelCI.

```
./kci_build install_kernel --config=next --kdir=linux
```

See the output in `linux/_install_`.

### 5. Optional: publish the kernel build

If you have a `kernelci-backend` instance running, you can send the kernel
binaries and also the meta-data with these commands:

```
./kci_build push_kernel \
  --kdir=linux --api=https://localhost:12345 --db-token=1234-5678

./kci_build publish_kernel \
  --kdir=linux --api=https://localhost:12345 --db-token=1234-5678
```

Alternatively, to store the meta-data locally in a JSON file:

```
./kci_build publish_kernel --kdir=linux --json-path=build-meta.json
```
