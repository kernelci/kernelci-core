---
title: "kci_rootfs"
date: 2021-08-05
draft: false
description: "Command line tool to build rootfs images"
weight: 5
---

### How to build a rootfs image using kci_rootfs

You will be using `kernelci/staging-debos` docker image for this purpose.

1. Pull the docker image `docker pull kernelci/staging-debos`

2. Clone the kernelci-core repo.

    ```
    git clone https://github.com/kernelci/kernelci-core.git
    ```
3. Start the docker and get into it.

   ```
   sudo docker run -itd -v $(pwd)/kernelci-core:/kernelci-core --device /dev/kvm --privileged kernelci/staging-debos
   sudo docker exec -it <container_id> bash
   cd /kernelci-core/
   ```
4. Now to check if everything works, type `./kci_rootfs --help` it should produce below help message.

    ```
    usage: kci_rootfs [-h] [--yaml-configs YAML_CONFIGS]

                      {validate,list_configs,list_variants,build,upload} ...
    optional arguments:
      -h, --help            show this help message and exit
      --yaml-configs YAML_CONFIGS
                            Path to the YAML configs file
    Commands:
      {validate,list_configs,list_variants,build,upload}
                            List of available commands
        validate            Validate the rootfs YAML configuration
        list_configs        List all rootfs config names
        list_variants       List all rootfs variants
        build               Build a rootfs image
        upload              Upload a rootfs image
    ```
5. To list available rootfs configuration, you can use `list_configs` option.

    ```
    $ ./kci_rootfs list_configs
    buster
    buster-v4l2
    buster-igt
    ```
   By default `kci_rootfs` reads entries from `rootfs-configs.yaml`. This file acts as a rootfs config file.

6. Let's list all available rootfs images using `./kci_rootfs list_variants`. It should show existing
rootfs name along with its architecture.

    ```
    buster amd64
    buster arm64
    ```

    It also comes with couple of options `--rootfs-config` and `--arch` to
    filter the results based on config name or arch type.

    ```
    $ ./kci_rootfs list_variants --rootfs-config buster --arch i386
    buster i386

    $ ./kci_rootfs list_variants --rootfs-config buster
    buster amd64
    buster arm64

    $ ./kci_rootfs list_variants --arch amd64
    buster amd64
    buster-v4l2 amd64
    buster-igt amd64
    ```
7. Now it's time to re-build existing rootfs image using `kci_rootfs build`. It
   takes three arguments:
    * `--rootfs-config` refers to rootfs name which you want to build
    * `--data-path` points to debos files location
    * `--arch` refers to CPU arch you want to build

    For example, to build a buster rootfs image for i386, you can run
    ```
    ./kci_rootfs build \
        --rootfs-config buster \
        --data-path config/rootfs/debos \
        --arch i386
    ```

   depending on your network speed, this will take some time to complete.

8. If build is successful you should see message like

    ```
    cd ${ROOTDIR} ; find -H  |  cpio -H newc -v -o | gzip -c - > ${ARTIFACTDIR}/buster/i386/rootfs.cpio.gz | ./build_info.json
    cd ${ROOTDIR} ; find -H  |  cpio -H newc -v -o | gzip -c - > ${ARTIFACTDIR}/buster/i386/rootfs.cpio.gz | 79539 blocks
    Powering off.
    ==== Recipe done ====
    ```
    Finally newly built rootfs images can be found under the directory pointed by `--data-path`. In our case, its `config/rootfs/debos/buster/i386/`

    ```
    $ ls config/rootfs/debos/buster/i386/
    build_info.json  full.rootfs.cpio.gz  full.rootfs.tar.xz  initrd.cpio.gz  rootfs.cpio.gz  rootfs.ext4.xz
    ```

### Create a new rootfs image

Now you know how to build default `kci_rootfs` images. Let's look at how to add simple `buster` rootfs image.

1. First you need to add appropriate entries to `rootfs_config.yml` file.

    ```
      buster-example:
        rootfs_type: debos
        debian_release: buster
        arch_list:
          - amd64
          - arm64
        extra_packages_remove:
          - e2fslibs
          - e2fsprogs
    ```

  Above entry will create rootfs named `buster-example` for CPU amd64 and arm64 architectures without `e2fslibs` and  `e2fsprogs` packages. List of possible `rootfs-config` yaml entries and its description are listed below:

  | Entry                 | Description |
  | ----------------------| ----------- |
  | buster-example        | Unique rootfs configuration name. |
  | rootfs_type           | Tool used for rootfs creation. |
  | debian_release        | Desired Debian OS version. |
  | arch_list             | Desired list of CPU architecture. |
  | extra_packages_remove | Specifies list of packages to remove from rootfs. |
  | script                | Custom script to be executed during rootfs image creation. |
  | test_overlay          | Create a directory layout on final rootfs image as provided. |
  | extra_packages        | Installs specified packages on rootfs image. |
  | extra_files_remove    | Removes specified files from rootfs image. |

  Please note at the moment, only `debos` is supported as `rootfs_type` and above options are debos specific.

2. Now validate `rootfs-config.yml` entries using `./kci_rootfs validate` and verify that it didn't report any errors.

3. If no issues reported during validation, start the build process using,

    ```
    ./kci_rootfs build \
        --rootfs-config buster-example \
        --data-path config/rootfs/debos \
        --arch amd64
    ```
    and wait for its completion. If everything went fine you should see
    something like below under `config/rootfs/debos/buster-example/amd64/`
    directory.

    ```
    ls config/rootfs/debos/buster-example/amd64/
    build_info.json  full.rootfs.cpio.gz  full.rootfs.tar.xz  initrd.cpio.gz  rootfs.cpio.gz  rootfs.ext4.xz
    ```
