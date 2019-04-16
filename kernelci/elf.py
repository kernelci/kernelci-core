# Copyright (C) 2017 Linaro Limited
# Author: Milo Casagrande <milo.casagrande@linaro.org>
# Author: Matt Hart <matthew.hart@linaro.org>
#
# Copyright (C) 2017 Baylibre SAS
# Author: Kevin Hilman <khilman@baylibre.com>
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

"""Open the ELF file and read some of its content."""

import elftools.elf.constants as elfconst
import elftools.elf.elffile as elffile
import io
import os

# Default section names and their build document keys to look in the ELF file.
# These are supposed to always be available.
DEFAULT_ELF_SECTIONS = [
    (".bss", "vmlinux_bss_size"),
    (".text", "vmlinux_text_size")
]

# Write/Alloc & Alloc constant we need to check for in the ELF sections.
ELF_WA_FLAG = elfconst.SH_FLAGS.SHF_WRITE | elfconst.SH_FLAGS.SHF_ALLOC
ELF_A_FLAG = elfconst.SH_FLAGS.SHF_ALLOC


def calculate_data_size(elf_file):
    """Loop through the ELF file sections and compute the .data size.

    It will look for all SHT_PROGBITS type sections that have the
    SHF_ALLOC or SHF_ALLOC+SHF_WRITE flag set and sum their sizes.

    :param elf_file: The open ELF file.
    :return The .data size or 0.
    """
    data_size = 0

    for section in elf_file.iter_sections():
        elf_flags = section["sh_flags"]
        if all([section["sh_type"] == "SHT_PROGBITS",
                any([elf_flags == ELF_WA_FLAG, elf_flags == ELF_A_FLAG])]):
            data_size += section["sh_size"]

    return data_size


def read(path):
    """Read a vmlinux file and extract some info from it.

    Update the build document in place.

    Info extracted:
        0. Size of the .text section.
        1. Size of the .data section.
        2. Size of the .bss section.

    :param path: The path to the vmlinux file.
    :type path: str
    :return A dictionary with the extracted values.
    """
    extracted = {}

    if os.path.isfile(path):
        with io.open(path, mode="rb") as vmlinux_strm:
            elf_file = elffile.ELFFile(vmlinux_strm)

            for elf_sect in DEFAULT_ELF_SECTIONS:
                sect = elf_file.get_section_by_name(elf_sect[0])
                if sect:
                    extracted[elf_sect[1]] = sect["sh_size"]

            data_sect = elf_file.get_section_by_name(".data")
            if data_sect:
                extracted["vmlinux_data_size"] = data_sect["sh_size"]
            else:
                extracted["vmlinux_data_size"] = \
                    calculate_data_size(elf_file)

    return extracted
