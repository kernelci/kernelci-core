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

import os

try:
    from scandir import walk
except ImportError:
    from os import walk


def parse_dtb_dir(build_dir, dtb_dir):
    """Parse the dtb directory of a build and return its contents.

    :param build_dir: The directory of the build that containes the dtb one.
    :type build_dir: string
    :param dtb_dir: The name of the dtb directory.
    :type dtb_dir: string
    :return A list with the relative path to the files contained in the dtb
    directory.
    """
    dtb_data = []
    d_dir = os.path.join(build_dir, dtb_dir)
    for dirname, subdirs, files in walk(d_dir):
        if not dirname.startswith("."):
            rel = os.path.relpath(dirname, d_dir)
            for f in files:
                if not f.startswith("."):
                    dtb_data.append(os.path.join(rel, f))
    return dtb_data
