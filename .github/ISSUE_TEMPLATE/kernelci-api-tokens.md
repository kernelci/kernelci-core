---
name: KernelCI API tokens
about: Request to get some KernelCI API tokens
title: Request API tokens for USER
labels: ''
assignees: ''

---

KernelCI uses kernelci-backend to manage its database which contains all the data about builds and tests.  There are 2 main instances, a production one for kernelci.org and a test one for staging.kernelci.org.  Separate tokens can be provided for either or both, with several permissions to choose from.  KernelCI labs will also typically need a token to be able to push their test results.

Please answer the questions below to request some API tokens:

**Contact details**

⇨ User name:

⇨ Email address:

If this is for a lab token:

⇨ Lab owner first and last names:

⇨ Lab name:

**Production**

The production instance is the one behind `https://kernelci.org`.  Production tokens are only provided for labs that are able to send useful data, or with read-only permissions to create dashboards or consume the results data in any way (stats, reports...).  Uses of the kernelci.org production data should ideally be made public.

The URL of the production API server is `https://api.kernelci.org`.

Do you need a token to access the production API?  If so, is this to be able to read the data or also send some test results from a lab?

⇨ Read-only or also to to push results:

**Staging**

The URL of the staging API server is `https://staging-api.kernelci.org`.

The staging instance is used for experimental features without impacting the production instance.  This is useful for anything new that needs to be tested in a full KernelCI environment with results publicly available on `https://staging.kernelci.org` but not sent to regular mailing lists.

Do you need a token to access the staging API?  If so, is this to be able to read the data or send some test results from a lab?

⇨ Read-only or also to push results:
