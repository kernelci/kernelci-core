---
title: "User settings"
date: 2021-08-05
draft: false
description: "User-defined local settings"
weight: 2
---

The user settings file is intended to be created by end-users with options
specific to their local setup.  It can also be used by automated CI systems, in
particular to hide secret API tokens.  The format is similar to
[INI](https://en.wikipedia.org/wiki/INI_file) although it is parsed by the
Python 3 [`configparser`](https://docs.python.org/3/library/configparser.html)
package.

The default name for the file is `kernelci.conf` and it has several standard
potential locations:

* `kernelci.conf` in the current working directory,
* `~/.config/kernelci/kernelci.conf` for per-user settings,
* `/etc/kernelci/kernelci.conf` for system-wide settings.

Unless directly specified on the command line with the `--settings` argument,
each of the default locations above will be visited in that order until one is
found to exist.  Only one settings file will be loaded, the first one found.

Settings are defined in separate sections within the file, as described in
detail below.  Regardless of what is set in the file, each option can always be
overridden on the command line.  So if you set `kdir: linux` in the settings
file as the default path to the Linux kernel source directory, you can always
override it with `--kdir=/some/other/path` on the command line (say, if you
want to occasionally use a different source tree).  This applies to all the
options as they are derived from the list of arguments supported by each
command.

There is a convention to convert the command line argument names to settings
names, with the `--` being dropped and single dashes `-` replaced with
underscores `_`.  This is identical to what the Python 3
[`argparse`](https://docs.python.org/3/howto/argparse.html) module does to
convert command line argument names to Python object attributes.  A few
examples:

* `--kdir` becomes `kdir`
* `--lab-config` becomes `lab_config`

To get started quickly, see the [kernelci.conf.sample](../kernelci.conf.sample)
file.  You can copy it as `kernelci.conf` into a suitable location as described
above and edit it to suit your particular needs.

## Command sections

Each command line tool will be looking for a section with a matching name in
the settings file, such as `[kci_build]`, `[kci_test]` or `[kci_data]`.  These
are not required to be in the file, but can be used to provide default values
for command line arguments.  For example:

```ini
[kci_build]

mirror: linux-mirror.git
kdir: linux
build_env: gcc-10
j: 3
```

With the values set above, instead of running this:
```
kci_build update_mirror --build-config=mainline --mirror=linux-mirror.git
```
you can now omit the `--mirror` argument:
```
kci_build update_mirror --build-config=mainline
```

## Component sections

Other sections are specific to a component, such as a test lab or a database
backend.  This is to allow different values to be set for a same option
depending on the component being used, and also to allow these values to be
used by all the command line tools.

The component names are derived from entries defined in the YAML configuration
files, such as `runtime-configs.yaml` or `db-configs.yaml`.  However, the
settings file can be used to keep values that don't belong in the YAML
configuration such as secret API tokens or arbitrary user-specific choices.

Each component section name in the settings file will be composed of two parts,
separated by a colon `:` character:

* a prefix with the type of component such as `lab` or `db`
* the name of the component

For example, if you define a lab called `my-lava-lab` in
`runtime-configs.yaml`, you can create a section called `[lab:my-lava-lab]` in
the settings file.  You can refer to it with `--lab-config=my-lava-lab` on the
command line, or even set `lab_config: my-lava-lab` in the `[DEFAULT]` section
to always pick this one by default.  Here's an example:

```ini
[DEFAULT]

lab_config: my-lava-lab

[lab:my-lava-lab]

user: user-name
lab_token: 1234-5678
```

## `[DEFAULT]` section

As per the INI file standard specifications, the `[DEFAULT]` section is where
catch-all default values can be set regardless of the settings section being
looked up.  The example above shows how this can be used, for a default
`lab_config` value across all the command line tools.  But values in the
`[DEFAULT]` section also apply to component sections.  Say, if you have set up
several labs but they all need the same user name to access their API, you can
set `user` in the `[DEFAULT]` section and not have to repeat it in each
`[lab:lab-name]` section.

### A more complete example

It's worth noting that for a same command, some settings values will be found
in a tool section such as `[kci_test]` while others will be found in a
component section such as `[lab:lab-name]`.  Others may be found in the
`[DEFAULT]` section, and finally any option can always be provided or
overridden on the command line.

For example, if you have these values in your `kernelci.conf` settings file:

```ini

[DEFAULT]

db_config: localhost

[db:localhost]

db_token: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
callback_id: kernelci-callback-local
callback_url: http://localhost:5001

[kci_build]

kdir: linux
build_env: gcc-10
```

you can then run these commands:

```
kci_build build_kernel --arch=arm64 --defconfig=defconfig
kci_build install_kernel --build-config=mainline
```

The `kci_build build_kernel` command normally requires `--kdir` and
`--build-env`, they are both defined in the `[kci_build]` section so they can
be dropped on the command line.  The `--arch` and `--defconfig` options are
still passed on the command line here, because they're more likely to change
between kernel builds.  If you build the same architecture and defconfig most
of the time, you can still set some default values for them under the
`[kci_build]` section and drop them from the command line too until you need to
build a different one.  Say if you mostly build `arm64`, you can set it in the
settings file, but if you need to build `x86_64` one day you can pass
`--arch=x86_64` on the command line without having to edit the settings file.

Then the `kci_build install_kernel` command normally requires `--kdir`,
`--db-token` and `--db-config`.  These can all be found in the settings file,
so they don't need to be provided on the command line: `db_config` is in the
`[DEFAULT]` section, `db_token` in the `[db:localhost]` section and `kdir` in
the `[kci_build]` section.
