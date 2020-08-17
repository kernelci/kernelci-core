## How to use LAVA with KernelCI

Any LAVA lab with a publicly available API can be added to kernelci.org.  Or,
if you have a private instance of KernelCI, you can set it up locally too.  The
KernelCI core tool [`kci_test`](kci_test.md) can be used to generate test job
definitions and submit them.  Then the
[kernelci-backend](https://github.com/kernelci/kernelci-backend) can receive
callback notification HTTP requests directly from LAVA and add the test results
to the database.


### Setting up a LAVA lab

A distributed LAVA lab is composed of a main server with a web frontend, and a
number of dispatchers which have a direct connection to the devices running
tests.  For KernelCI development purposes, typically a self-contained LAVA lab
can be set up with a server and a single dispatcher with at least one QEMU
device instance.

LAVA can be installed natively using Debian packages as per the [LAVA
documentation](https://docs.lavasoftware.org/lava/pipeline-server.html).
Another convenient way to do this is using the [KernelCI LAVA
Docker](https://github.com/kernelci/lava-docker) containers.


### Steps to add a LAVA lab to kernelci.org

Once you have a LAVA lab up and running, follow these steps to start running
`kernelci.org` tests:

1. Create a `kernel-ci` user as per the [LAVA
documentation](https://docs.lavasoftware.org/lava/simple-admin.html#index-11)
1. Create a LAVA API authentication token as per the [LAVA
documentation](https://docs.lavasoftware.org/lava/first_steps.html#index-1) for
the `kernel-ci` user.  It will be used for submitting jobs using `kci_test`,
either manually or automatically via Jenkins.
1. Create another LAVA API authentication token for the `kernel-ci` user with
   the description set to `kernel-ci-bisection-webhook` for automated
   bisection via Jenkins.
1. Create a GitHub pull request to add your lab definition to
   [`lab-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/master/lab-configs.yaml).
1. Optionally, create another GitHub pull request to add device definitions in
   [`test-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/master/test-configs.yaml)
   if your lab has new device types not already covered by kernelci.org.
1. A maintainer will get in touch with you to provide the LAVA API tokens and
   give you some KernelCI backend API tokens for your lab.  They will be used
   for LAVA callback
   [notifications](https://docs.lavasoftware.org/lava/user-notifications.html#index-0).
1. Store the backend API tokens for in LAVA for the `kernel-ci` user using
   `kernel-ci-callback` and `kernel-ci-callback-staging` respectively as their
   descriptions.

Your lab will then start being used on
[staging.kernelci.org](https://staging.kernelci.org) to verify it's all working
as expected.  Jobs will be scheduled automatically every 8h, and the results
will start appearing on the web dashboard and in email reports.  Then it will
normally get enabled in production [kernelci.org](https://kernelci.org) to run
tests for all the trees and test suites enabled for your lab (or everything by
default).
