---
title: "kci_test"
date: 2021-08-05
draft: false
description: "Command line tool to generate and run tests"
weight: 6
---

## `kci_test`

The output of `kci_build` can be used with the
[`kci_test`](https://github.com/kernelci/kernelci-core/blob/main/kci_test) tool
to generate and submit test definitions.  It will be using the meta-data JSON
files produced by `kci_build` and will also need to communicate with the test
labs where to run the tests.  Currently, only
[LAVA](https://www.lavasoftware.org/) is fully supported but other types of
labs and runtime environments may be added (LabGrid, Kubernetes...).  Test
configurations can be found in
[`test-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/main/config/core/test-configs.yaml)
with the list of test plans and which devices should run them.  Likewise, the
lab configurations can be found in
[`lab-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/main/config/core/lab-configs.yaml)
and database backend configurations in
[`db-configs.yaml`](https://github.com/kernelci/kernelci-core/blob/main/config/core/db-configs.yaml)

Each lab is typically expected to have a remote API available with a URL and a
user authentication token.  Running `kci_test` does not strictly require
anything else than the kernel binaries with metadata and a lab to run tests,
typically LAVA.  If a `kernelci-backend` instance is available, it can be used
to store test results.

The example below uses the build output from the commands shown in the
`kci_build` [documentation](../kci_build) section to generate and submit tests
in a lab:

### 1. Optional: save a local copy of any lab-specific data

Generating test definitions relies on some information that may specific to the
particular lab where the jobs need to be submitted.  For example, some labs
have non-standard device type names and use aliases.  Retrieving this
information every time a job definition is generated can result in a
significant overhead while in practice it doesn't change very often.

To avoid repeating the same queries with the labs, the `kci_test get_lab_info`
command can be used to store it locally in a JSON file and then reuse it with
subsequent commands.  This is mostly useful when running automated jobs that
will determine when to get the information again (say, once for each kernel
revision being built, or once every hour...).  When submitting only a few jobs
manually, the overhead may not be so much of a problem.

Here's a sample command to get the data from a lab and store it in a JSON file:

```
./kci_test get_lab_info \
  --user=kernelci-user-name \
  --lab-config=lab-name \
  --lab-token=abcd-7890 \
  --lab-json=lab-name.json
```

It's good practice to rely on a [settings](../settings) file to store secret
tokens and other static options.  For example, in a local `kernelci.conf` file:

```ini
[lab:lab-name]
user: kernelci-user-name
lab_token: abcd-7890
lab_json: lab-name.json
```

Then with this settings file, the command line becomes:

```
./kci_test get_lab_info --lab-config=lab-name
```

### 2. Generate test definitions

The `kci_test generate` command will generate test definitions for a given set
of build meta-data and a given lab.  It can either generate all the compatible
test definitions based on the `test_config` entries in `test-configs.yaml`, or
a subset of it, or a single arbitrary one specified entirely on the command
line.

The `--callback-id` and `--callback-url` options are only used to get a
callback from the test lab to a service able to receive it.  It is not required
to generate and run a job as the results may be shared by other means or
manually retrieved depending on the runtime environment.

To generate the definitions for all the jobs that can be run in a lab:

```
./kci_test generate \
  --db-config=localhost \
  --install-path=linux/_install_/ \
  --lab-config=lab-name \
  --output=jobs \
  --storage=https://some-storage-place.com/ \
  --user=kernelci-user-name \
  --lab-token=abcd-7890 \
  --lab-json=lab-name.json \
  --callback-id=kernelci-callback \
  --callback-url=https://callback-recipient.com/handler/
```

Once again, a [settings](../settings) file can be used to simplify the command
line:

```ini
[DEFAULT]
storage: https://some-storage-place.com/
db_config: localhost
lab_config: lab-name

[lab:lab-name]
user: kernelci-user-name
lab-token: abcd-7890
lab-json: lab-name.json

[db:localhost]
db_token: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
api: http://192.168.0.123:5001
callback-id: kernelci-callback
callback-url: https://192.168.0.123:12345
```

Now the command line becomes:

```
./kci_test generate --install-path=linux/_install_ --output=jobs
```


Extra options can be added to generate only a subset of those jobs, filtering
by test plan, target or machine type respectively.  For example:

```
--plan=baseline
```

```
--target=odroid-xu3
```

```
--mach=qemu
```

It's also possible to generate one job definition with an arbitrary combination
of test plan and target, even if it is not listed in any `test_config` entry in
the YAML configuration.  Also, when `--output` is not specified, the job
definitions are printed on stdout.  Here's an example of how to generate such a
job definition:

```
./kci_test generate
  --install-path=linux/_install_ \
  --plan=baseline_qemu \
  --target=qemu_arm64-virt-gicv3 \
  > job.yaml
```

### 3. Submit tests

Once the test job definitions have been generated and stored in some files,
they can be submitted to the test lab with the `kci_test submit` command.
Still relying on the same settings file to simplify the command line:

```
./kci_test submit --lab-config=lab-name --jobs=jobs/*
```

What happens next depends on where the test was submitted.  Typically, jobs run
in LAVA send a callback when they complete and a `kernelci-backend` instance
will receive them to import the test results into the database.  But this is
not a requirement, other types of runtime environment may be sending their
results differently.

In a local development environment, the user may choose to receive the callback
directly.  For example, this can be done by running `nc -l -p 12345 >
callback.json` and using a plain HTTP URL to the host such as
`--callback-url=http://192.168.0.123:12345`.
