# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Open the ELF file and read some of its content."""

import elftools.elf.constants as elfconst
import elftools.elf.elffile as elffile
import io
import os

import models

# Default section names and their build document keys to look in the ELF file.
# These are supposed to always be available.
DEFAULT_ELF_SECTIONS = [
    (".bss", models.VMLINUX_BSS_SIZE_KEY),
    (".txt", models.VMLINUX_TEXT_SIZE_KEY)
]


def calculate_data_size(elf_file):
    """Loop through the ELF file sections and compute the .data size.

    If will look for all SHT_PROGBITS type sections that have only the
    SHF_ALLOC flag set and sum their sizes.

    :param elf_file: The open ELF file.
    :return The .data size or 0.
    """
    data_size = 0

    for section in elf_file.iter_sections():
        if all([section["sh_type"] == "SHT_PROGBITS",
                section["sh_flags"] == elfconst.SH_FLAGS.SHF_ALLOC]):
            data_size += section["sh_size"]

    return data_size


def read(build_doc, build_dir):
    """Read a vmlinux file and extract some info from it.

    Update the build document in place.

    Info extracted:
        0. Size of the .text section.
        1. Size of the .data section.
        2. Size of the .bss section.
    """
    vmlinux = os.path.join(build_dir, build_doc.vmlinux_file)

    if os.path.isfile(vmlinux):
        with io.open(vmlinux, mode="rb") as vmlinux_strm:
            elf_file = elffile.ELFFile(vmlinux_strm)

            for elf_sect in DEFAULT_ELF_SECTIONS:
                sect = elf_file.get_section_by_name(elf_sect[1])
                if sect:
                    setattr(build_doc, elf_sect[1], sect["sh_size"])

            data_sect = elf_file.get_section_by_name(".data")
            if data_sect:
                setattr(
                    build_doc,
                    models.VMLINUX_DATA_SIZE_KEY, data_sect["sh_size"])
            else:
                setattr(
                    build_doc,
                    models.VMLINUX_DATA_SIZE_KEY,
                    calculate_data_size(elf_file)
                )
