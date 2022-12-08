---
title: "Contributing Guidelines"
date: 2022-12-08T09:21:56Z
draft: true
weight: 3
---

KernelCI core project is open for contributions. Contributions may consist of
adding new build, tests and device types as well as features and bugfixes for
KernelCI core tools.
The best way to contribute is to send a PR to [kernelci-core](https://github.com/kernelci/kernelci-core).
When the PR is created, [KernelCI staging](https://kernelci.org/docs/instances/staging)
instance takes care of updating the [staging.kernelci.org branch](https://github.com/kernelci/kernelci-core/tree/staging.kernelci.org).
In general the branch is updated every 8h and a limited set of builds and tests
is run on it. More detailed information about the logic behind staging runs can
be found [here](https://kernelci.org/docs/instances/staging).

There are several guidelines which can facilitate the PR review process.

1. Make sure the PR is well described
   1. Describe the purpose of the changes
   2. Example use cases are welcome
2. Attach staging build/test results when possible
   1. Staging instance is updated every 8h. If the PR is expected to produce build/test results
   check [staging dashboard](https://staging.kernelci.org) and make sure these are mentioned in the PR comment
   2. If the results are not visible, but they should be, mention it in the comments, too
3. Make sure that reviewers' comments and questions are addressed
   1. When there are comments unanswered for more than 1 month the PR will be closed
4. In case there is a need to consult the PR with KernelCI maintainers join the open hours
   1. Open hours take place every Thursday at 12:00 UTC at KernelCI [Jitsi](https://meet.kernel.social/kernelci-dev)
5. You can reach KernelCI maintainers also at:
   1. IRC - #kernelci channel on [libera.chat](https://libera.chat/)
   2. KernelCI mailing list - [kernelci@lists.linux.dev](mailto:kernelci@lists.linux.dev)
