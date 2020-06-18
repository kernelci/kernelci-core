## Development workflow using staging.kernelci.org

While the production instance is hosted on
[kernelci.org](https://kernelci.org), another independent instance is hosted on
[staging.kernelci.org](https://staging.kernelci.org).  This is where all the
changes to the code and configuration get tested before updating production.
It consists of Jenkins,
[`kernelci-backend`](https://github.com/kernelci/kernelci-backend) for the
Mongo DB and REST API, and
[`kernelci-frontend`](https://github.com/kernelci/kernelci-frontend) for the
web dashboard.

Jobs are run every 8h on staging, using all the code from pull requests.  It
will build a dedicated kernel branch based on
[linux-next](https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git)
but with only a small number of configurations, and get some tests run in all
the labs.

### GitHub pull requests

A special feature of the staging instance is the ability to test code from
pending GitHub pull requests before they get merged.  This is handled by tools
in the [`kernelci-deploy`](https://github.com/kernelci/kernelci-deploy)
project, to pull all the open pull requests for a given project, apply some
arbitrary patches and push the resulting `staging.kernelci.org` branch back to
the repository.  This branch is being replaced (force-pushed) every time the
tool is run.

Things to note:

* Pull requests are only merged from users that are on a trusted list, stored
  in the `kernelci-deploy` configuration files.
* Pull requests are merged in chronological order, so older ones take
  precedence.
* Pull requests that fail to merge are ignored and will not be tested.
* Pull requests will be skipped and not merged if they have the `staging-skip`
  label set.
* If any patch from `kernelci-deploy` doesn't apply, the resulting branch is
  not pushed.  It is required that all the patches always apply since some of
  them are necessary to adjust the staging behaviour (say, to not send
  bisection email reports).  They will need to get updated if they conflict
  with pending PRs.
* A tag is created with the current date and pushed with the branch.


### Jenkins: bot.staging.kernelci.org

The staging instance is running Jenkins, just like production.  The main
difference is that the staging one is publicly visible, read-only for anonymous
users: [bot.staging.kernelci.org](https://bot.staging.kernelci.org/)

This allows for the job logs to be inspected.  Also, some developers have a
personal folder there to run modified versions of the Jenkins job but still
using the available resources (builders, API tokens to submit jobs in test
labs...).


### Run every 8h

There is a timer on the staging.kernelci.org server which starts a job every
8h, so 3 times per day.  The job does the following:

1. update [staging branch for `kernelci-jenkins`](https://github.com/kernelci/kernelci-jenkins/tree/staging.kernelci.org)
1. recreate Jenkins jobs by running the job-dsl "seed" job
1. update [staging branch for `kernelci-core`](https://github.com/kernelci/kernelci-core/tree/staging.kernelci.org)
1. update [staging branch for `kernelci-backend`](https://github.com/kernelci/kernelci-backend/tree/staging.kernelci.org)
1. update the `kernelci-backend` service using Ansible from [`kernelci-backend-config`](https://github.com/kernelci/kernelci-backend-config) with the staging branch
1. update [staging branch for `kernelci-frontend`](https://github.com/kernelci/kernelci-frontend/tree/staging.kernelci.org)
1. update the `kernelci-frontend` service using Ansible from [`kernelci-frontend-config`](https://github.com/kernelci/kernelci-frontend-config) with the staging branch
1. create and push a `staging.kernelci.org` branch with a tag to the [kernelci Linux kernel repo](https://github.com/kernelci/linux)
1. trigger a monitor job in Jenkins with the [`kernelci_staging`](https://github.com/kernelci/kernelci-core/blob/staging.kernelci.org/build-configs.yaml#L612) config

The last step should cause the monitor job to detect that the staging kernel
branch has been updated, and run a kernel build trigger job which in turn will
cause tests to be run.  Builds and test results will be sent to the staging
backend instance, and results will be available on the staging web dashboard.
Regressions will cause bisections to be run on the staging instance, and
results to be sent to the
[`kernelci-results-staging@groups.io`](https://groups.io/g/kernelci-results-staging)
mailing list.
