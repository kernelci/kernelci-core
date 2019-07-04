# Welcome to KernelCI

This repository provides the core functions used on
[kernelci.org](https://kernelci.org) to monitor upstream Linux kernel branches,
build many kernel variants, run tests, run bisections and schedule email
reports.

This software can also be used to set up an independent instance and to build
any arbitrary kernel branches and run any arbitrary tests.

You can find some general information as well as detailed technical
instructions on the KernelCI
[wiki](https://github.com/kernelci/kernelci-doc/wiki/KernelCI).


# Contents of this repository


## Configuration files

All the builds are configured in [`build-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/master/build-configs.yaml), with the list of
branches to monitor and which kernel variants to build for each of them.

Then all the tests are configured in [`test-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/master/test-configs.yaml) with the list of
devices, test suites and which tests to run on which devices.

Details for the format of these files can be found on the wiki pages for
[build configurations](https://github.com/kernelci/kernelci-doc/wiki/Build-configurations)
and [test configurations](https://github.com/kernelci/kernelci-doc/wiki/Test-configurations).


## Python modules

There are Python modules in the `kernelci` package to parse and use the
configuration data from the YAML files, as well as the
[`kci_build`](https://github.com/kernelci/kernelci-core/blob/master/kci_build)
command line tool to access this data directly and implement automated build
jobs.  Each module has some Python docstrings and the command line tool has
detailed help messages for each command it can run.


## Jenkins jobs

All the automated jobs on kernelci.org are run in Jenkins.  Some legacy scripts
are still being used in "freestyle" projects but they are gradually being
replaced with Pipeline jobs.  Each Pipeline job has a `.jpl` file located in
the `jenkins` directory:

* [`jenkins/monitor.jpl`](https://github.com/kernelci/kernelci-core/tree/master/jenkins/monitor.jpl) to monitor kernel branches
* [`jenkins/build-trigger.jpl`](https://github.com/kernelci/kernelci-core/tree/master/jenkins/build-trigger.jpl) to trigger all the builds for a kernel revision
* [`jenkins/build.jpl`](https://github.com/kernelci/kernelci-core/tree/master/jenkins/build.jpl) to build each individual kernel
* [`jenkins/bisect.jpl`](https://github.com/kernelci/kernelci-core/tree/master/jenkins/bisect.jpl) to run boot bisections
* [`jenkins/buster.jpl`](https://github.com/kernelci/kernelci-core/tree/master/jenkins/buster.jpl) to build a Debian Buster file system

There are other variants based on `stretch.jpl` to build other file systems
with extra tools needed to run specific test suites.

In addition to the job files, there are also some common library files located
in the
[`src/org/kernelci`](https://github.com/kernelci/kernelci-core/tree/master/src/org/kernelci)
directory.


## Dockerfiles

Each Jenkins Pipeline job runs in a Docker container.  The Docker images used
by these containers are built from `jenkins/dockerfiles` and pushed to the
[`kernelci Docker repositories`](https://cloud.docker.com/u/kernelci/repository/list).


## Test templates

The kernelci.org tests typically run in [LAVA](https://lavasoftware.org/).
Each LAVA test is generated using template files which can be found in the
[`templates`](https://github.com/kernelci/kernelci-core/tree/master/templates)
directory.

# Reproducing KernelCI steps locally

It's possible to reproduce KernelCI builds locally, see the
[KernelCI command line](https://github.com/kernelci/kernelci-doc/wiki/KernelCI-command-line)
wiki page.

All the KernelCI steps are being gradually refactored into command line tools
in order to be able to run them in a terminal, or in any automation system
rather than just Jenkins.  The next steps to be added are to generate and
submit test jobs and to run bisections.
