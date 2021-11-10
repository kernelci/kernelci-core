<img src="https://kernelci.org/image/kernelci-horizontal-color.png"
     alt="KernelCI project logo"
     width="40%" />

# Welcome to KernelCI

The KernelCI project is dedicated to testing the upstream Linux kernel.  Its
mission statement is defined as follows:

> To ensure the quality, stability and long-term maintenance of the Linux
> kernel by maintaining an open ecosystem around test automation practices and
> principles.

The main instance of KernelCI is available on
[kernelci.org](https://kernelci.org).

There is also a separate instance used for KernelCI development available on
[staging.kernelci.org](https://staging.kernelci.org), see [Development
workflow](doc/staging.md) for all the details about it.

This repository provides core functions to monitor upstream Linux kernel
branches, build many kernel variants, run tests, run bisections and schedule
email reports.

It is also possible to set up an independent instance to build any arbitrary
kernel and run any arbitrary tests.

You can find some more general information about the KernelCI project on the
[wiki](https://github.com/kernelci/kernelci-doc/wiki/KernelCI).


## User guide

KernelCI users will typically want to add their kernel branch to be monitored,
connect their lab or send results from their own existing CI system.  The pages
below are a work-in-progress to cover all these topics:

* [Using LAVA with KernelCI](https://kernelci.org/docs/labs/lava/)


## Command line tools

All the steps of the KernelCI pipeline are implemented with portable command
line tools.  They are used in [Jenkins pipeline
jobs](https://github.com/kernelci/kernelci-jenkins/tree/master/jobs) for
kernelci.org, but can also be run by hand in a shell or integrated with any CI
environment.  The
[`kernelci/build-base`](https://hub.docker.com/r/kernelci/build-base) Docker
image comes with all the dependencies needed.

**The available command line tools are:**

* **[`kci_build`](doc/kci_build.md)** to get the kernel source code, create a
  config file, build kernels and push them to a storage server.

* **[`kci_test`](doc/kci_test.md)** to generate and submit test definitions in
  an automated test lab.

* **[`kci_rootfs`](doc/kci_rootfs.md)** to build a CPU specific rootfs image
  for given OS variant and push them to a storage server.

**Other command line tools are being worked on** to replace the current legacy
implementation which is still tied to Jenkins or hard-coded in shell scripts:

* **`kci_data` (WIP)** to submit KernelCI data to a database and retrieve it.

* **`kci_bisect` (WIP)** to run KernelCI automated bisections.

* **`kci_email` (WIP)** to generate an email report with test results.


## [User Settings file](doc/settings.md)

The command line tools can make use of an optional settings file with
user-specific options.  These settings provide default values for any of the
command line arguments, as a convenience but also to avoid providing secrets
such as API tokens in clear.  The file uses sections for each command line tool
and also for each component (i.e. each lab, backend...).

See the [`kernelci.conf.sample`](kernelci.conf.sample) sample config file and
the [user settings file](doc/settings.md) section for more details about how
this works.

## YAML Configuration files

All the builds are configured in
[`build-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/master/build-configs.yaml),
with the list of branches to monitor and which kernel variants to build for
each of them.

Then all the tests are configured in
[`test-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/master/test-configs.yaml)
with the list of devices, test suites and which tests to run on which devices.

Details for the format of these files can be found on the wiki pages for [build
configurations](https://github.com/kernelci/kernelci-doc/wiki/Build-configurations)
and [test
configurations](https://github.com/kernelci/kernelci-doc/wiki/Test-configurations).


## Python package on PyPI

The [`kernelci` package on PyPI](https://pypi.org/project/kernelci/) contains
all the modules from the `kernelci` directory as well as the `kci_*` command
line tools.  This provides the core functions of KernelCI, to parse YAML
configuration and perform each step of the pipeline such as building kernels,
running tests and sending results to a database.


## Dockerfiles

Each step of the KernelCI Pipeline can be run in a Docker container.  On
[kernelci.org](https://kernelci.org), this is done in Jenkins jobs.  The Docker
images used by these containers are built from `jenkins/dockerfiles` and pushed
to the [`kernelci Docker
repositories`](https://cloud.docker.com/u/kernelci/repository/list).


## Test templates

The majority of [kernelci.org](https://kernelci.org) tests get run in
[LAVA](https://lavasoftware.org/), although this is not a requirement.  Each
LAVA test is generated using template files which can be found in the
[`templates`](https://github.com/kernelci/kernelci-core/tree/master/templates)
directory.
