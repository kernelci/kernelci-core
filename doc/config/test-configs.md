---
title: "Test Configurations"
date: 2021-08-03
draft: false
description: "How to configure tests"
weight: 3
---

All the top-level test configurations are contained in a YAML file:
[`test-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/main/config/core/test-configs.yaml).
This defines everything that can be run on test platforms.  The primary
use-case is to generate and submit test job definitions as done by
[`kci_test`](../../kci_test).

There are several sections in this file:

* **file systems** are user-space archives with more or less test utilities
  installed
* **device types** are test platforms
* **test plans** are test cases to be run as a group
* **test configurations** are combinations of all of the above

The test configurations are the main entries as they define which tests
actually have to be run.  They refer to entries in other sections of the file
in order to provide some full combinations, for example to define that an
`igt-kms-exynos` test plan using a `bullseye-igt` file system should be run on an
`odroid-xu3` device.

In addition to those sections, there are some filters (passlist, blocklist) to
fine tune which tests should be run.  For example, some platforms are not
supported in older stable kernel branches so they'll typically have a blocklist
to only run tests with newer kernels.

## How to add a device type

Each device type has an entry in the `device_types` dictionary.  Here's an
example:

```yaml
device_types:

  beagle_xm:
    name: 'beagle-xm'
    mach: omap2
    class: arm-dtb
    boot_method: uboot
    dtb: 'omap3-beagle-xm.dtb'
    filters:
      - blocklist: *allmodconfig_filter
      - blocklist: {kernel: ['v3.14']}
```

The attributes are:
* `name` needs to match what test labs use to identify the platform.
* `mach` is to define a family of SoCs, originally from the `arch/arm/mach-*`
  board file names.
* `class` is used here to define a particular class of devices such as
  `arm-dtb` or `arm64-dtb`.
* `arch` is to define the CPU architecture following the Linux kernel names
  (`arm64`, `riscv`, `x86_64`...).  It is not required with the `arm-dtb` class
  as it is already specific to the `arm` architecture.
* `boot_method` is to define how to boot the device (`uboot`, `grub`...).
* `dtb` is an optional attribute to specify the name of the device tree.  By
  default, device types of the `arm-dtb` and `arm64-dtb` class will use `name`
  if there is no explicit `dtb` attribute.
* `filters` is an arbitrary list of filters to only run tests with certain
  configuration combinations.  See the [filters section](../#filters) for more
  details.
* `flags` is an arbitrary list of strings with properties of the device type,
  to also filter out some job configurations.  See the [Flags](#flags) section
  below for more details.

Note: In this example, the class is architecture-specific so it also defines
the `arch` value which is why it does not appear here.

### Filter options

Test configuration filters may use any of the following options:

* `arch` is the CPU architecture name
* `defconfig` is the full defconfig name
* `kernel` is the full kernel version name
* `build_environment` is basically the compiler name
* `tree` is the name of the kernel git tree (e.g. `mainline`, `next`...)
* `branch` is the name of the kernel git branch
* `lab` is the lab name

### Default filters

In order to avoid duplicating or referencing the same filters repeatedly, there
are some default filters which apply to all test configurations.  Any filter
explicitly defined will take precedence over the default ones.

* `test_plan_default_filters`

This filter definition acts as the default for all test plans.  It's
essentially there to only test the relevant defconfig for each arch
(i.e. multi_v7_defconfig on arm, defconfig on arm64 etc...).

* `device_default_filters`

Similarly, this defines the default filters for all the devices.  Typically it
disables things that can't be run on most devices, such as the `allmodconfig`
kernel builds as they are too large to boot from a ramdisk with all the
modules.  With some architectures, they are known to not really boot anyway.

### Flags

Device types can also have a list of flags, for example:

```yaml
device_types:

  meson_gxbb_p200:
    name: 'meson-gxbb-p200'
    mach: amlogic
    class: arm64-dtb
    boot_method: uboot
    flags: ['lpae', 'big_endian']
    filters:
      - blocklist: {defconfig: ['allnoconfig', 'allmodconfig']}
```

This can then be used to filter out some jobs, for example `kci_test` will pass
the `big_endian` flag when the kernel build was for big-endian.

Flags currently in use are:
* `big_endian` to tell whether the device can boot big-endian kernels
* `lpae` to tell whether the device can boot kernels built with LPAE enabled
  (Large Physical Address Extension for ARMv7)
* `fastboot` to tell whether the device can boot with fastboot (stored in jobs
  meta-data but not actively used)

## How to configure a test plan

Each test plan has a set of template files, and an entry in the `test_plans`
dictionary.  Typically, tests are for LAVA and the templates are stored in the
[`config/lava`](https://github.com/kernelci/kernelci-core/blob/main/config/lava).
Test plans rely on rootfs definitions, so here's a simplified example:

```yaml
file_systems:

  debian_bullseye_ramdisk:
    type: debian
    ramdisk: 'bullseye/20210909/{arch}/rootfs.cpio.gz'

test_plans:

  sleep:
    rootfs: debian_bullseye_ramdisk
    params:
      sleep_params: mem freeze
```

It's required to specify a `rootfs` attribute which points to an entry in the
`file_systems` dictionary.  The root file system should contain all the tools
and test suites required to run the test plan.

When generating test job definitions, the path to the test template file is
created using this default pattern:

```python
'{plan}/{category}-{method}-{protocol}-{rootfs}-{plan}-template.jinja2'
```

The `plan` and `rootfs` values are coming from the test plan definition.  The
other values are coming from the test platform (determined later at runtime)
and file system type definitions: `method` is the boot method, `protocol` is
how to download the kernel etc.

So when adding a test plan, typically there will be one template with only the
test steps and other templates inheriting it to add configuration specific
steps.  For example, still with the [`sleep` test
plan](https://github.com/kernelci/kernelci-core/blob/main/config/lava/sleep/):

```bash
generic-barebox-tftp-ramdisk-sleep-template.jinja2
generic-depthcharge-tftp-ramdisk-sleep-template.jinja2
generic-uboot-tftp-ramdisk-sleep-template.jinja2
sleep.jinja2
```

There are 3 templates to run this test plan on devices that can boot either
with U-Boot, Barebox or Depthcharge.  They all include the test steps defined
in `sleep.jinja2`.

## How to add a test configuration

Defining device types, file systems and test plans is necessary but not
sufficient to run tests.  There also need to be an entry in `test_configs` to
bind together a device with a list of test plans.  For example, this device
type is configured to run several test plans:

```yaml
test_configs:

  - device_type: bcm2836-rpi-2-b
    test_plans:
      - baseline
      - ltp-crypto
      - sleep
      - usb
```

It's possible to have several entries with the same `device_type` to define
special filters.  For example, if some tests need to only be run on that device
in a specific lab, or with a specific defconfig or tree etc.  Here's an example
to run all tests on any kernel except `igt` which should only be on kernels
more recent than `v4.14` (i.e. `v4.19` LTS onwards):

```yaml
test_configs:

  - device_type: rk3399-gru-kevin
    test_plans:
      - baseline
      - baseline-nfs
      - cros-ec
      - ltp-fcntl-locktests
      - ltp-pty
      - ltp-timers
      - sleep
      - v4l2-compliance-uvc

  - device_type: rk3399-gru-kevin
    test_plans:
      - igt-gpu-panfrost
      - igt-kms-rockchip
    filters:
      - blocklist: {kernel: ['v3.', 'v4.4', 'v4.9', 'v4.14']}
```

## How to add a file system configuration

File systems contain all the user-space files.  They are required to include
the necessary dependencies in order to run the test suites associated with
them.

Each file system has a type to define the base URL and architecture names.  For
example, here's the `buildroot` type:

```yaml
file_system_types:

  buildroot:
    url: 'http://storage.kernelci.org/images/rootfs/buildroot/kci-2020.05-6-g8983f3b738df'
    arch_map:
      arm64be: [{arch: arm64, endian: big}]
      armeb:   [{arch: arm,   endian: big}]
      armel:   [{arch: arm}]
      x86:     [{arch: i386}, {arch: x86_64}]
      mipsel:  [{arch: mips}]
```

* `url` is the base URL where the file systems can be downloaded.
* `arch_map` is a dictionary to translate kernel CPU architecture names into
  file system specific names.

Then file systems can be defined for each type, with some additional
information to work out the full URL of each variant.  For example:

```yaml
file_systems:

  buildroot_ramdisk:
    type: buildroot
    ramdisk: '{arch}/base/rootfs.cpio.gz'

  debian_bullseye_nfs:
    type: debian
    ramdisk: 'bullseye/20210909/{arch}/initrd.cpio.gz'
    nfs: 'bullseye/20210909/{arch}/full.rootfs.tar.xz'
    root_type: nfs
```

These file systems use different types: `buildroot` and `debian`, so they have
different base URLs and different `arch_map` attributes as each distro has its
own architecture naming convention.  The file system configs each provide a
different URL for their different variants (ramdisk and NFS in this case).  The
URL names such as `ramdisk` or `nfs` are arbitrary and used by `kci_test` to
render templates into test job definitions.  The `{arch}` template value will
be replaced by one of the entries in the `arch_map` for the file system type or
the regular kernel one.
