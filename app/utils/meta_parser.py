# Copyright (C) 2014 Linaro Ltd.
#
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

"""Functions to parse build metadata files."""

import ConfigParser

from utils import LOG

CONFIG_FILE_START = '[default]'
CONFIG_FILE_DEFAULT = 'DEFAULT'


def parse_metadata_file(metadata_file):
    """Parse the build metadata file.

    No checks are performed on the file: it must exists and be a valid file.

    :param metadata_file: Full path to the file to parse.
    :return A dictionary with the key-values found in the metadata file, None
        otherwise.
    """
    metadata = None

    with open(metadata_file, 'r') as r_file:
        first_line = r_file.readline()

        if first_line.strip().lower() == CONFIG_FILE_START:
            r_file.seek(0)
            metadata = _parse_config_metadata(r_file)
        else:
            r_file.seek(0)
            metadata = _parse_build_metadata(r_file)

    return metadata


def _parse_config_metadata(metadata_file):
    """Parse a INI-like metadata file.

    Only the default section in the file will be read.

    :param metadata_file: The open for reading metadata file.
    :return A dictionary containing the parsed lines in the file.
    """
    LOG.info("Parsing metadata file %s", metadata_file)

    config = ConfigParser.ConfigParser(allow_no_value=True)
    config.readfp(metadata_file)

    metadata = {
        k: v for k, v in config.items(CONFIG_FILE_DEFAULT)
    }

    return metadata


def _parse_build_metadata(metadata_file):
    """Parse the metadata file contained in thie build directory.

    :param metadata_file: The open for reading metadata file.
    :return A dictionary containing the parsed lines in the file.
    """
    metadata = {}

    LOG.info("Parsing metadata file %s", metadata_file)

    for line in metadata_file:
        line = line.strip()
        if line:
            if line[0] == '#':
                # Accept a sane char for commented lines.
                continue

            try:
                key, value = line.split(':', 1)
                value = value.strip()
                if value:
                    # We store only real values, not empty ones.
                    metadata[key] = value
            except ValueError, ex:
                LOG.error("Error parsing metadata file line: %s", line)
                LOG.exception(str(ex))

    return metadata
