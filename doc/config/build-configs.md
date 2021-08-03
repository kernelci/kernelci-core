---
title: "Build configurations"
date: 2021-08-03
draft: false
description: "YAML build configurations"
---

All the top-level build configurations are contained in a YAML file:
[`build-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/main/config/core/build-configs.yaml). This
defines all the kernels that need to be built, with some attributes to cover
all the details and variants.

There are several types of entries in this file:

 - *trees* are git repositories
 - *config fragments* are modular lists of kernel config values
 - *build environments* define the available compilers
 - *architectures* are to keep all the properties related to each CPU
   architecture build variants are to define a set of builds done within a
   build configuration
 - *build configurations* are combinations of all of the above

The build configurations are the main entries as they define what is actually
going to be built. They must have one tree and one branch defined, and
optionally more details such as which compilers to use, which architectures and
defconfigs to build etc. There should not be more than one build config with a
given tree / branch combination to avoid monitoring the same branch more than
once. Each build entry can have several build variants as sub-sections to
define multiple ways of building a same branch.

### How to add trees and branches

Each tree is defined in the `trees` section. So to add a new tree, that is to
say a new git repository, add an entry such as this one with the name of the
tree and its URL:

```yaml
  renesas:
    url: "https://git.kernel.org/pub/scm/linux/kernel/git/geert/renesas-devel.git"
```

Then to start monitoring and building branches from that tree, a build config
needs to be added for each branch in the `build_configs` section.  For example,
in this tree we're monitoring 2 branches:

```yaml
  renesas:
    tree: renesas
    branch: 'devel'

  renesas_next:
    tree: renesas
    branch: 'next'
```

The build configuration names typically follow the `tree_branch` convention, or
just `tree` if only one branch is being monitored.  This is purely a convention
to avoid having the same branch monitored twice and to make it easier to
maintain.  The name is not encoding any actual information as the actual tree
and branch names are defined in attributes.

### How to define build variants

There is a `build_configs_defaults` entry which acts as a default for the build
variants used in build configs. If a `variants` dictionary is defined in a
build config it will override the default. Build variants are defined as a
dictionary to allow several different ones for each tree / branch
configuration. They need to have a `build_environment` attribute referring to a
build environment definition and a list of architectures to build with any
extra attributes needed to define what needs to be built.

Here's an example for the media tree which only builds 4 architectures and
enables a special config fragment virtualvideo:

```yaml
  media:
    tree: media
    branch: 'master'
    variants:
      gcc-7:
        build_environment: gcc-7
        fragments: [virtualvideo]
        architectures:
          i386: *i386_arch
          x86_64: *x86_64_arch
          arm: *arm_arch
          arm64: *arm64_arch
```

It uses YAML anchors such as `*arm_arch` to refer to the default definitions
for that architecture. It's also possible to override that to only build a
subset of the default configuration, for example to only build the defconfig on
arm64 and x86_64:

```yaml
        architectures:
          arm64:
            filters:
              - whitelist: {defconfig: ['defconfig']}
          x86_64:
            base_defconfig: 'x86_64_defconfig'
            filters:
              - whitelist: {defconfig: ['x86_64_defconfig']}
```
