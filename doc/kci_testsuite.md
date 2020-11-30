This page contains details about how to add a test suite to KernelCI and how it can be used in a LAVA environment.

### Verify your requirement:

-  First validate whether you really need to create a new rootfs images. You can find existing rootfs variants using
  `kci_rootfs list_variants`. If any of those matches your requirements, please make use of it.

-  If you want to make some minor modification, then check the options below:
     - If you need to install some Debian packages, have look at `extra_packages` option in `rootfs-configs.yaml` file.
     - To install a specific test suite built from source or any arbitrary commands, have a look at the `script` option in `rootfs-configs.yml` file. It allows to you
        run prepare rootfs image in a desired manner.
     - To install arbitrary files such as helper scripts or test input data in some specific locations, have a look at the `overlay` option in `rootfs-configs.yml`.


### How to add test suite to a rootfs image

1. Let's understand how a test suite can be added to a rootfs image. For this, we will explore the `buster-v4l2` rootfs image.

2. Take a look at `rootfs-configs.yaml` for `buster-v4l2`. It should display the following config entries:


```
  buster-v4l2:
    rootfs_type: debos
    debian_release: buster
    arch_list:
      - amd64
      - arm64
      - armhf
    extra_packages_remove:
      - bash
      - e2fslibs
      - e2fsprogs
    script: "scripts/buster-v4l2.sh"
    test_overlay: "overlays/v4l2"
```


3. We will look into last three config entries, namely: `extra_packages_remove`, `script` and `test_overlay`.

   `extra_packages_remove` as its name suggests will remove the listed packages from the final rootfs image. In this case,
    packages like `bash`, `e2fslibs` and `e2fsprogs` are deleted from the image.

4. Understand that `script` path is relative to the `kci_rootfs build --data-path` value. By default this is `jenkins/debian/debos/script`
   Lets have quick look at its current contents:

```
$ ls -1 jenkins/debian/debos/scripts/

buster-cros-ec-tests.sh
buster-igt.sh
buster-v4l2.sh
create_initrd_ramdisk.sh
create_manifest.py
crush.sh
nothing.sh
setup-networking.sh
stretch-ltp.sh
strip.sh
```

   Let's focus on `buster-v4l2.sh` for this example. If you peek into the script you will find that it performs actions like installing packages via apt-get, setting
   up v4l2 build directories and building and installing the v4l2 binaries. It's just a normal bash script not tied to debos or KernelCI.


   If you would like to run the `buster-v4l2.sh` script and verify manually, simply copy the script to `debian:buster` docker image and execute it.

5. The `test_overlay` option is used to create a specific directory layout inside the rootfs image. In our case:

```
$ tree jenkins/debian/debos/overlays/v4l2/
jenkins/debian/debos/overlays/v4l2/
└── usr
    └── bin
        └── v4l2-parser.sh

```
   `/usr/bin/v4l2-parser.sh` will be available in the `buster-v4l2` rootfs image. These overlay scripts are normally run from LAVA job to execute some tests and parse the results.
    This sample [LAVA job definition](https://lava.collabora.co.uk/scheduler/job/2446126/definition#defline120) shows how `v4l2-parser.sh` can be used.


6. Hopefully now you should have some basic idea about how to add a test suite to a rootfs and how it can be used in LAVA environment.

### How to add a new test suite to a buster rootfs image

For this example, we will be using the `btrfs-progs` test-suite.

1. Let's first modify `rootfs-configs.yaml` to add `buster-btrfs` with appropriate entries.

```
  buster-btrfs:
    rootfs_type: debos
    debian_release: buster
    arch_list:
      - amd64
    script: "scripts/buster-btrfs.sh"
    test_overlay: "overlays/btrfs"
    extra_files_remove: *extra_files_remove_buster
```


We will now look into some config entries, namely: `extra_packages`, `script` and `test_overlay`.
2. `extra_packages` as its name suggests will add the listed packages to the final rootfs image. As we don't need any additional packages this option can be ommited in our config.

3. `script` is the path to an arbitrary script to run in the root file system.  This is typically used to build some test
    suites from source.  Remember that its path is relative to the `kci_rootfs build --data-path` value, which by default is
   `jenkins/debian/debos/script`. In this example, we need to add new script named `buster-btrfs.sh`. It's a simple script
    to clone the repository, then build and install.

```
$ cat jenkins/debian/debos/script/buster-btrfs.sh

#!/bin/bash
set -e

BUILD_DEPS="pkg-config git make autoconf automake gcc \
make libblkid-dev zlib1g-dev liblzo2-dev libzstd-dev e2fslibs-dev python3-setuptools python3.7-dev"

apt-get update && apt-get install -y $BUILD_DEPS
GIT_SSL_NO_VERIFY=1 git clone --depth=1 https://github.com/kdave/btrfs-progs.git /btrfs-progs
cd /btrfs-progs
./autogen.sh
./configure --disable-documentation
make
make install
apt-get purge -y $BUILD_DEPS && apt-get autoremove -y

```


4. The `test_overlay` option is used to create specific directory layout inside the rootfs image. In our case:

```
$ tree jenkins/debian/debos/overlays/btrfs/
jenkins/debian/debos/overlays/btrfs/
└── usr
    └── bin
        └── btrfs-verify-cli.sh
```

   `/usr/bin/btrfs-verify-cli.sh` will be available in the `buster-btrfs` rootfs image. These overlay scripts are normally ran from a LAVA job.

```
$ cat jenkins/debian/debos/overlays/btrfs/btrfs-verify-cli.sh

cd  /btrfs-progs && TEST=001\* ./tests/cli-tests.sh
```

5. Make sure execute permission is applied on the scripts. 

```
chmod +x jenkins/debian/debos/overlays/btrfs/usr/bin/btrfs-verify-cli.sh
chmod +x jenkins/debian/debos/scripts/buster-btrfs.sh
```

6. Now build `buster-btrfs` rootfs image using kci_rootfs like:

```
./kci_rootfs build --rootfs-config buster-btrfs --data-path jenkins/debian/debos --arch amd64
```

If you would like to read more about `kci_rootfs`, please check the `kci_rootfs` [documentation](https://github.com/kernelci/kernelci-core/blob/master/doc/kci_rootfs.md)

7. Once the rootfs image is created, you can use it with an appropriate kernel image and on a compatible target architecture (`amd64` for `x86_64` in this case). Make sure that the kernel config has
   appropriate btrfs configs and other file system specific entries enabled. 

8. Add appropriate test entry to the LAVA job definition in order to run `btrfs-verify-cli.sh`. For example,

```
run:
    steps:
        - lava-test-case test-btrfs-cli-001 --shell ls /usr/bin/btrfs-verify-cli.sh

```

If you would like to read more about LAVA job definitions, please check the LAVA documentation part about [writing tests](https://docs.lavasoftware.org/lava/writing-tests.html)

How to add tests to LAVA
========================

Prerequisites
-------------

- Rootfs image is built 
- Rootfs image boots on a platform
- Tests can be run

If you're facing issues with tha above you may want to go through the section "How to add test suite to a rootfs image"

Adding new test plan to LAVA
------------------------------

1. Use the rootfs image to boot the device and produce a LAVA job definition for the tests.
Upload rootfs image to kernelci-backend (storage)

```
kci_rootfs upload --rootfs-dir /path/to/rootf/image/ --upload-path server/path --api http://api.kernelci --db-token KCI_API_TOKEN
```

Add rootfs definition to `test-configs.yaml`

```yaml
  debian_buster_btrfs_ramdisk:
    type: debian
    ramdisk: 'buster-btrfs/{arch}/rootfs.cpio.gz'
```

**Note**
`ramdisk` path must be relative to storage server URL as defined in a `file_system_types` section of `test-configs.yaml`

If you need to define a filesystem type you may want to have a look at `file_system_types` section of `test-configs.yaml`

e.g.

```yaml
debian:
    url: 'http://yourstorage/path/to/images/debian/'
    arch_map:
      armhf: [{arch: arm}]
      amd64: [{arch: x86_64}]
```

Detailed description of the test configuration can be found [here](https://github.com/kernelci/kernelci-doc/wiki/Test-configurations)

2. Add LAVA job definition template

Create appropriate directory structure under `templates` directory.

```
mkdir templates/btrfs/
```

Create test plan definition

```
cat templates/btrfs/btrfs.jinja2
```

```yaml
- test:
    timeout:
      minutes: 10
    definitions:
    - repository:
        metadata:
          format: Lava-Test Test Definition 1.0
          name: {{ plan }}
          description: "btrfs test plan"
          os:
          - debian
          scope:
          - functional
        run:
          steps:
          - lava-test-case test-btrfs-cli-001 --shell ls /usr/bin/btrfs-verify-cli.sh
      from: inline
      name: {{ plan }}
      path: inline/{{ plan }}.yaml
```


```
cat templates/btrfs/generic-qemu-btrfs-template.jinja2
```

```
{% extends 'boot/generic-qemu-boot-template.jinja2' %}
{% block actions %}
{{ super () }}

{% include 'btrfs/btrfs.jinja2' %}

{% endblock %}

{%- block image_arg %}
        image_arg: '-kernel {kernel} -append "console={{ console_dev }},115200 root=/dev/ram0 debug verbose {{ extra_kernel_args }}"'
{%- endblock %}
```

3. Update `test-plans` section of `test-configs.yaml` with new test definition


```yaml
  btrfs:
    rootfs: debian_buster_btrfs_ramdisk
    pattern: 'btrfs/generic-qemu-btrfs-template.jinja2'
```

4. Use `kci_build` to build the kernel and `kci_test` to run the tests in a LAVA lab.

Build the Kernel

```
kci_build build_kernel --kdir /path/to/linux --arch x86_64 --build-env gcc-8 --verbose -j 4
```

Genrate test job definitions

```
kci_test generate --bmeta-json /path/to/bmeta.json --dtbs-json /path/to/artifacts/dtbs.json --lab-json /path/to/mgalka-lava-local.json --storage http://storage.kernelci --lab-config your-lab-name --user lava_user --lab-token LAVA_API_TOKEN --output /output/path --callback-id your-lava-callback-name --callback-url http://api.kernelci
```

**Note** 

Make sure that there is that the lab you chose to supports the type of tests which you've just defined. You may need to modify `lab-configs.yaml` accordingly.

e.g.

```yaml
  your-local-lab:
    lab_type: lava
    url: 'http://kernelci-lava/RPC2/'
    filters:
      - passlist:
          plan:
            - baseline
            - btrfs
```


Submit test jobs

```
kci_test submit --lab-config your-lab-name --user lava_user --lab-token LAVA_API_TOKEN --jobs /path/to/generated/test/job/definitions
```

5. Create PR to add the test plan