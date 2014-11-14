#!/usr/bin/python
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

import models.boot as mboot
import utils.bootimport
import utils.db


def main():
    database = utils.db.get_db_connection({})

    board = "fake-board"
    job = "next"
    kernel = "next-20141113"
    defconfig = "u8500_defconfig"
    lab_name = "lab-01"

    boot_doc = mboot.BootDocument(board, job, kernel, defconfig, lab_name)
    utils.bootimport._update_boot_doc_ids(boot_doc, database)

    print boot_doc.defconfig_id
    print boot_doc.job_id
    print boot_doc.to_dict()

if __name__ == '__main__':
    main()
