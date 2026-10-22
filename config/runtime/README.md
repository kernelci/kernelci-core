# Runtime templates

## QEMU container image for LAVA

The `boot/qemu.jinja2` template uses `kernelci/qemu` by default. To use a
mirror or another compatible QEMU image, set `qemu_docker_image` in a
platform's `params`:

```yaml
platforms:
  qemu-arm64:
    arch: arm64
    boot_method: qemu
    context:
      arch: arm64
    params:
      qemu_docker_image: registry.example.com:5000/kernelci/qemu:stable
```

A job can also set the parameter. Job parameters take precedence over
platform parameters:

```yaml
jobs:
  baseline:
    template: base/lava.jinja2
    params:
      boot_commands: ramdisk
      test_method: baseline
      ramdiskroot: https://example.com/rootfs
      qemu_docker_image: registry.example.com/kernelci/qemu:stable
```

Use a complete container image reference, including an optional registry,
port, tag or digest. An omitted, null or empty value uses `kernelci/qemu`.
The selected image must provide the platform's `qemu-system-<arch>` binary
and be accessible to the LAVA worker. This parameter selects the boot
action's container image; it is separate from the job's top-level `image`
setting for its runtime environment.
