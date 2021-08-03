---
title: "Filters"
date: 2021-08-03
draft: false
description: "Configuration filters"
---

Filters are implemented in
[`kernelci.config.base`](https://github.com/kernelci/kernelci-core/blob/main/kernelci/config/base.py)
and all have a `match()` method to determine whether a set of configuration
options are compatible with the filter definition.  It will basically return
`True` if the options match the filter or `False` otherwise.

There are several types of filters:

* **passlist** to only run a test if all the filter conditions are met

```yaml
  - passlist: {defconfig: ['bcm2835_defconfig']}
```

In this example, the filter will return `True` if `bcm2835_defconfig` is in the
`defconfig` name.

* **blocklist** to not run a test if any of the filter conditions is met

```yaml
  - blocklist: {lab: ['lab-baylibre']}
```

In this example, the filter will return `False` if `lab-baylibre` is in the
`lab` name.

* **combination** to only run a test if a given set of values is present in the
  filter conditions

```yaml
  - combination: &arch_defconfig_filter
      keys: ['arch', 'defconfig']
      values:
        - ['arm', 'multi_v7_defconfig']
        - ['arm64', 'defconfig']
        - ['x86', 'x86_64_defconfig']
```

In this example, the filter will return `True` only if the provided `arch` and
`defconfig` pair exactly matches one of the 3 defined combinations defined in
`values`.
