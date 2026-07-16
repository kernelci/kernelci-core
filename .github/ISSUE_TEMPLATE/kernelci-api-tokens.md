---
name: KernelCI API accounts
about: Request a KernelCI (Maestro) API account
title: Request API account for USER
labels: ''
assignees: ''

---

KernelCI uses the [Maestro API](https://github.com/kernelci/kernelci-api) to manage its database which contains all the data about builds and tests.  There are 2 main instances, a production one for kernelci.org and a staging one for testing changes.  Access is based on user accounts: an admin sends you an invitation link, you set a password and then obtain API tokens by logging in.  Reading data doesn't require any account or token, so this is only needed to send data to the API.

Lab owners connecting their lab to KernelCI typically need an account for [pull labs](https://docs.kernelci.org/components/maestro/pipeline/connecting-pull-lab/), which poll the API for jobs and push their test results.  [LAVA labs](https://docs.kernelci.org/components/maestro/pipeline/connecting-lab/) don't need an API account: they use a callback token generated in the lab itself and added to the pipeline configuration.

Please answer the questions below to request an account:

**Contact details**

⇨ User name:

⇨ Email address:

If this is for a lab:

⇨ Lab owner first and last names:

⇨ Lab name:

⇨ Lab type (pull lab or LAVA):

**Production**

The production instance is the one behind `https://kernelci.org`.  Production accounts are only provided for labs and services that are able to send useful data.  Reading the production data doesn't require an account.

The URL of the production API server is `https://api.kernelci.org`.

⇨ Do you need an account on the production API?

**Staging**

The URL of the staging API server is `https://staging.kernelci.org:9000`.

The staging instance is used for experimental features without impacting the production instance.  This is useful for anything new that needs to be tested in a full KernelCI environment before moving to production.

⇨ Do you need an account on the staging API?
