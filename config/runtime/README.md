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

## ARM64 QEMU ACPI boot

Set `qemu_arm64_acpi: true` in a LAVA job's `params` to boot an existing
ARM64 QEMU platform with UEFI and ACPI:

```yaml
jobs:
  baseline-arm64-qualcomm:
    template: baseline.jinja2
    kind: job
    kcidb_test_suite: boot
    params:
      rootfs_ref: buildroot-baseline
      qemu_arm64_acpi: true
```

The flag applies only to platforms with `boot_method: qemu` and `arch: arm64`.
It appends `-bios /usr/share/qemu-efi-aarch64/QEMU_EFI.fd` to the generated
LAVA context's `extra_options` and adds `acpi=force` to QEMU's kernel command
line. It does not modify the shared platform configuration. Omitted or
false flags preserve the existing boot behavior.

Deploy the updated core templates together with the pipeline configuration.
The QEMU container must contain the firmware at that path; rebuild the image
with the updated QEMU recipe, which installs `qemu-efi-aarch64`, or use a
compatible image via `qemu_docker_image`. The kernel must enable `CONFIG_ACPI`,
`CONFIG_EFI`, and `CONFIG_EFI_STUB`. The pipeline baseline test checks for a
readable `/sys/firmware/acpi/tables/DSDT` when this mode is active, so a boot
without usable ACPI tables does not pass that check.
