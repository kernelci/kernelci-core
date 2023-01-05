#!/usr/bin/env python3
#
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (C) 2022 Collabora Limited
# Author: Denys Fedoryshchenko <denys.f@collabora.com>
#

import sys
import os
import platform

ACPI_VARIANTS = ["/sys/bus/platform/drivers/chromeos_acpi/GOOG0016:00",
                 "/sys/bus/platform/drivers/chromeos_acpi/GGL0001:00"]
NVRAM_DEVICE = "/dev/nvram"
VB2_NV_CLEAR_TPM_OWNER_REQUEST = 0x1
VB2_NV_OFFS_TPM = 0x5

FDT_BASE_PATH = "/proc/device-tree/firmware/chromeos"
SECTOR_SIZE = 512

nv_offset = -1
nv_size = -1
NV_TPM_OFFSET = -1
NV_CRC_OFFSET = -1

commit_reset = False

def reflect_data(x, width):
    # See: https://stackoverflow.com/a/20918545
    if width == 8:
        x = ((x & 0x55) << 1) | ((x & 0xAA) >> 1)
        x = ((x & 0x33) << 2) | ((x & 0xCC) >> 2)
        x = ((x & 0x0F) << 4) | ((x & 0xF0) >> 4)
    elif width == 16:
        x = ((x & 0x5555) << 1) | ((x & 0xAAAA) >> 1)
        x = ((x & 0x3333) << 2) | ((x & 0xCCCC) >> 2)
        x = ((x & 0x0F0F) << 4) | ((x & 0xF0F0) >> 4)
        x = ((x & 0x00FF) << 8) | ((x & 0xFF00) >> 8)
    elif width == 32:
        x = ((x & 0x55555555) << 1) | ((x & 0xAAAAAAAA) >> 1)
        x = ((x & 0x33333333) << 2) | ((x & 0xCCCCCCCC) >> 2)
        x = ((x & 0x0F0F0F0F) << 4) | ((x & 0xF0F0F0F0) >> 4)
        x = ((x & 0x00FF00FF) << 8) | ((x & 0xFF00FF00) >> 8)
        x = ((x & 0x0000FFFF) << 16) | ((x & 0xFFFF0000) >> 16)
    else:
        raise ValueError('Unsupported width')
    return x


def crc_poly(data, n, poly, crc=0, ref_in=False, ref_out=False, xor_out=0):
    g = 1 << n | poly  # Generator polynomial

    # Loop over the data
    for d in data:
        # Reverse the input byte if the flag is true
        if ref_in:
            d = reflect_data(d, 8)

        # XOR the top byte in the CRC with the input byte
        crc ^= d << (n - 8)

        # Loop over all the bits in the byte
        for _ in range(8):
            # Start by shifting the CRC, so we can check for the top bit
            crc <<= 1

            # XOR the CRC if the top bit is 1
            if crc & (1 << n):
                crc ^= g

    # Reverse the output if the flag is true
    if ref_out:
        crc = reflect_data(crc, n)

    return crc


def crc8itu(msg):
    crc = crc_poly(msg, 8, 0x07, xor_out=0x55)
    return crc


def read_sysfs_file(filename):
    try:
        with open(filename, 'r') as f:
            output = f.read().strip()
    except Exception as e:
        print(f'File {filename} missing? error: {e}')
        sys.exit(1)
    return output


def read_nvram(fh):
    nvram = bytearray()
    while 1:
        try:
            b = fh.read(1)
        except Exception as e:
            print(f'Exception during nvram read:{e}')
            break
        if not b:
            break
        nvram += b
    return nvram


def verify_nvram(nvram):
    global nv_offset, nv_size, NV_TPM_OFFSET, NV_CRC_OFFSET
    nvram_len = len(nvram)
    if nvram_len < nv_offset+nv_size:
        print("NVRAM data too short, failing")
        sys.exit(3)

    print('Initial NVRAM read:')
    print(f'NVRAM total len {nvram_len}')
    print('START {:02x}'.format(nvram[0]))
    print('HDR {:02x}'.format(nvram[nv_offset]))
    print('TPM {:02x}'.format(nvram[NV_TPM_OFFSET]))
    print('CRC {:02x}'.format(nvram[NV_CRC_OFFSET]))
    calculated_crc = crc8itu(nvram[nv_offset:NV_CRC_OFFSET])
    print('CALCULATED CRC {:02x}'.format(calculated_crc))
    if nvram[NV_CRC_OFFSET] != calculated_crc:
        print("CRC mismatch, exiting to not damage NVRAM")
        sys.exit(4)


def program_nvram(nvram, fh):
    global nv_offset, nv_size, NV_TPM_OFFSET, NV_CRC_OFFSET
    print('Programming NVRAM flag...')
    # Clear TPM request flag
    nvram[NV_TPM_OFFSET] = VB2_NV_CLEAR_TPM_OWNER_REQUEST
    # Recalculate CRC entry in NVRAM
    nvram[nv_offset+nv_size-1] = crc8itu(nvram[nv_offset:NV_CRC_OFFSET])
    # if fh set
    if fh:
        # Write down relevant entries in character device
        fh.seek(NV_TPM_OFFSET)
        fh.write(bytes([nvram[NV_TPM_OFFSET]]))
        fh.seek(NV_CRC_OFFSET)
        fh.write(bytes([nvram[NV_CRC_OFFSET]]))
    else:
        print("No file handle, skipping write")
    
    return nvram

def tpm_reset_x86():
    global nv_offset, nv_size, NV_TPM_OFFSET, NV_CRC_OFFSET
    p_vendor = read_sysfs_file("/sys/class/dmi/id/sys_vendor")
    p_name = read_sysfs_file("/sys/class/dmi/id/product_name")
    nv_offset = -1
    nv_size = -1

    for a_dir in ACPI_VARIANTS:
        if os.path.exists(a_dir):
            nv_offset = read_sysfs_file(a_dir+"/VBNV.0")
            nv_size = read_sysfs_file(a_dir+"/VBNV.1")

    if nv_offset == -1 or nv_size == -1:
        print("ACPI variables not found (chromeos_acpi not enabled or not Chrome device)")
        sys.exit(2)

    # Thats just debug if troubleshooting will be required
    print(f'var["{p_vendor}_{p_name}"]["offset"]={nv_offset}')
    print(f'var["{p_vendor}_{p_name}"]["size"]={nv_size}')

    # Offset where ChromeOS NVRAM data is set
    nv_offset = int(nv_offset)
    # Size of ChromeOS specific "chunk"
    nv_size = int(nv_size)
    # CRC is always last byte
    NV_CRC_OFFSET = nv_offset+nv_size-1
    # TPM is 5th byte in ChromeOS "chunk"
    NV_TPM_OFFSET = nv_offset+VB2_NV_OFFS_TPM

    # Verify if offsets valid
    if NV_CRC_OFFSET < 0 or NV_TPM_OFFSET < 0:
        print("NVRAM offsets not valid")
        sys.exit(3)

    # Check if NVRAM_DEVICE exists
    if not os.path.exists(NVRAM_DEVICE):
        print("NVRAM device not found, kernel option missing?")
        sys.exit(4)

    with open(NVRAM_DEVICE, "r+b", 0) as fh:
        nvram = read_nvram(fh)
        verify_nvram(nvram)
        if commit_reset:
            nvram = program_nvram(nvram, fh)
        else:
            return
    print("Re-verification read after programming")
    with open(NVRAM_DEVICE, "r+b", 0) as fh:
        nvram = read_nvram(fh)
        verify_nvram(nvram)

# iterate over /sys/block/mmcblk%d/removable
#  and find the first one that is 0
# this is the eMMC device
# from src/platform/vboot_reference/host/arch/arm/lib/crossystem_arch.c
# FindEmmcDev
def find_emmc_device():
    for i in range(0, 10):
        removable = read_sysfs_file(f'/sys/block/mmcblk{i}/removable')
        if removable == '0':
            return f'/dev/mmcblk{i}'

    print('Unable to find eMMC device')
    sys.exit(1)

def read_fdt_property(property):
    with open(FDT_BASE_PATH + "/" + property, 'rb') as f:
        data = f.read()
        # convert data to int network byte order
        return int.from_bytes(data, byteorder='big')

def read_arm64_nvram():
    emmc_device = find_emmc_device()
    lba = read_fdt_property("nonvolatile-context-lba")
    offset = read_fdt_property("nonvolatile-context-offset")
    size = read_fdt_property("nonvolatile-context-size")
    # check if device size is big enough
    if lba * SECTOR_SIZE + offset + size > os.path.getsize(emmc_device):
        print('Device size is too small, offset+size > device size')
        sys.exit(6)
    with open(emmc_device, "r+b", 0) as fh:
        fh.seek(lba * SECTOR_SIZE + offset)
        nvram = fh.read(size)
        return nvram

def write_arm64_nvram(nvram):
    emmc_device = find_emmc_device()
    lba = read_fdt_property("nonvolatile-context-lba")
    offset = read_fdt_property("nonvolatile-context-offset")
    size = read_fdt_property("nonvolatile-context-size")
    # check if device size is big enough
    if lba * SECTOR_SIZE + offset + size > os.path.getsize(emmc_device):
        print('Device size is too small, offset+size > device size')
        sys.exit(6)
    with open(emmc_device, "r+b", 0) as fh:
        fh.seek(lba * SECTOR_SIZE + offset)
        fh.write(nvram)

# arm64
def tpm_reset_arm64():
    nvram = read_arm64_nvram()
    verify_nvram(nvram)
    if commit_reset:
        updated_nvram = program_nvram(nvram, None)
        write_arm64_nvram(updated_nvram)

def main():
    # print usage
    print(f'Usage: {sys.argv[0]} [-r]')
    print('  -r: reset TPM (default: verify only)')
    # if flag -r is set, reset TPM
    if len(sys.argv) > 1 and sys.argv[1] == '-r':
        commit_reset = True
    # Detect architecture
    arch = platform.machine()
    if arch == 'x86_64':
        print('x86_64 architecture detected')
        tpm_reset_x86()
    elif arch == 'aarch64':
        print('aarch64 architecture detected')
        tpm_reset_arm64()
    else:
        print(f'Unsupported architecture {arch}')
        sys.exit(5)

if __name__ == '__main__':
    main()
