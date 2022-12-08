---
title: "kci_data"
date: 2021-08-04
draft: false
description: "Command line tool to handle KernelCI data"
weight: 5
---

The [`kci_data`](https://github.com/kernelci/kernelci-core/blob/main/kci_data)
tool is mainly used to submit kernel build meta-data and test results to the
KernelCI backend.  It is still a work in progress, as the majority of native
test results are being sent via the LAVA callback mechanism which bypasses
kci_data with the current implementation.

The
[`db-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/main/config/core/db-configs.yaml)
file contains configuration for all the KernelCI databases that may be used
with `kci_data`.  They all have an API type, currently only `kernelci_backend`
is supported but this may change as new ones get added.  In particular, KCIDB
may be added there as a consolidation with the
[`kcidb`](https://github.com/kernelci/kcidb) command line tools.  The backend
used with native tests is also planned to get redesigned from scratch as the
project keeps evolving, so that would be a new API type too.

## Settings

Typically, database APIs require some authentication token.  The ideal way to
handle this is to use the [settings file](../settings) with an entry for each
`db` config to use.  While the `db-configs.yaml` configuration will include
general configuration information, the settings file is user-specific.  For
example, when using a `kernelci_backend` instance locally, the token can be
stored as such in the settings file:

```ini
[db:localhost]
db_token: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
api: http://192.168.122.1:5001
```

Note: At the moment, the `api` setting (or `--api` command line argument) also
needs to be provided even though it's effectively the same thing as the `url`
parameter in `db-configs.yaml`.  This is a legacy from before `kci_data` was
created, and it will eventually be dropped.  In the meantime, both need to be
provided with the same API URL.

## Submitting build meta-data

One common `kci_data` use-case is to submit the meta-data associated with a
kernel build.  This includes all the JSON files created by `kci_build`.  It
requires either the `kdir` argument for a local build to find the JSON
meta-data in the default `_install_` directory, or `output` if the files were
stored elsewhere.  With the database API token and URL stored in the settings
file as explained in the previous section, here's a typical command line:

```
./kci_data submit_build --db-config=localhost --kdir=linux
```

See also the [example in the `kci_build`
documentation](../kci_build/#5-optional-push-and-publish-the-kernel-build).

## Submitting test results

Test results can be submitted arbitrarily using `kci_data`.  It takes a JSON
file with the results, for example:

```json
{
    "job": "mainline",
    "git_branch": "master",
    "git_commit": "d012a7190fc1fd72ed48911e77ca97ba4521bccd",
    "kernel" : "v5.9-rc2",

    "build_environment": "gcc-10",
    "arch": "arm64",
    "defconfig": "defconfig",
    "defconfig_full": "defconfig",

    "lab_name": "gtucker-kci-data",
    "device_type": "qemu",

    "name": "v4l2-compliance-vivid",
    "test_cases": [
        {
            "name": "device-presence",
            "status": "PASS"
        }
    ],
    "sub_groups": [
        {
            "name": "Buffer-ioctls-Input-0",
            "test_cases": [
                {
                    "name": "VIDIOC_EXPBUF",
                    "status": "PASS"
                },
                {
                    "name": "Requests",
                    "status": "FAIL"
                }
            ]
        }
    ],
    "log": "Fake log\nJust some text\nNo parsing"
}
```

The schema allows a series of test cases with nested sub-groups which can also
include test cases.

When stored in a file e.g. `kci-data-v4l2-sample-results.json`, a typical
command to submit the results would be:

```
./kci_data submit_test --db-config=staging.kernelci.org --data-file=kci-data-v4l2-sample-results.json
{"code":201,"reason":"Test group 'v4l2-compliance-vivid' created","result":[{"_id":{"$oid":"5f44b88fd6ae1367ab1d3e5d"}}]}
```

The results can now be seen on the staging dashboard: \
[Results for v4l2-compliance-vivid: «v5.9-rc2» on
«qemu»](https://staging.kernelci.org/test/plan/id/5f44b88fd6ae1367ab1d3e5d/)

The example above was run with `--db-config=staging.kernelci.org` which implies
having an API token for the KernelCI staging API.  This was useful to be able
to show the results on the web dashboard.  The same command can be run with a
local instance using `--db-config=localhost`.

## Creating new API user (experimental)

We can create users for the new [KernelCI API](/docs/api) using `kci_data`.
This is still under development and it's not used in production by KernelCI.

An API token with admin permissions is required in order to do this, please see
the documentation about [how to create
one](/docs/api/api-details/#create-an-api-token-with-security-scopes).

For security reasons, instead of providing `--db-token` from the command line
we can add `db_token` in the [settings file](../settings) e.g. `kernelci.conf`:

```ini
[db:api]

db_token: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
```

Here's a sample command to create a regular user:

```
./kci_data create_user --username test --password test --db-config api
```

To create an admin user, add the `--is-admin` argument:

```
./kci_data create_user --username admin --password admin --db-config api --is-admin
```
