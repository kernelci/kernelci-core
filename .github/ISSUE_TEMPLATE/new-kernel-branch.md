---
name: New kernel branch
about: Add a kernel git branch to kernelci.org
title: Add branch BRANCH from TREE
labels: ''
assignees: ''

---

Each git kernel branch is monitored every hour by kernelci.org.  Whenever a new
revision is detected, it will be built for a number of combinations of
architectures, defconfigs and compilers.  Then a build report will be sent,
some tests will be run and test reports will also be sent.

Please provide the information described below in order to add a new branch to
kernelci.org:

- **How much build coverage do you need for your branch?**

Generally speaking, a good rule is to build fewer variants for branches that
are "further" away from mainline and closer to individual developers.  This can
be fine-tuned with arbitrary filters, but essentially there are 3 main options:

1. Build everything, including allmodconfig, which amounts to about 220 builds.
This is we do with linux-next.

2. Skip a few things such as allmodconfig as it's very long to build and
doesn't really boot, and also architectures that are less useful such as MIPS
which saves 80 builds and doesn't have much test platforms in KernelCI.  This
is we do with some subsystems such as linux-media.

3. Build only the main defconfig for each architecture to save a lot of build
power, get the fastest results and highest boots/builds ratio.  This is what do
with some maintainer branches such as linusw' GPIO branch.

⇨ Choice:

- **How often do you expect this branch to be updated?**

If you push once a week or less, it's easier to allow for many build variants
as this reduces the build load on average.  Conversely, if you push several
times every day then a small set of builds should be used.

It's also possible to increase the build capacity if needed but this comes with
a cost.  Avoiding unnecessary builds is always a good way to reduce turnaround
time and not waste resources.

⇨ Estimated frequency:

- **Who should the email reports be sent to?**

Standard email reports inlude builds and basic tests that are run on all
platforms. Please provide a list of email recipients for these.  Typical ones
are the regular KernelCI reports list, kernel mailing lists associated with the
changes going into the branch and related maintainers.

⇨ Recipients:
