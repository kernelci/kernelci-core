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

import glob
import os
import pymongo
import re

from bson import tz_util
from datetime import (
    datetime,
    timedelta
)

from models import DB_NAME
from models.boot import BootDocument
from utils import (
    BASE_PATH,
    LOG,
)
from utils.db import save

# Pattern used for glob matching files on the filesystem.
BOOT_REPORT_PATTERN = '*-boot-report.log'

RE_TREE_BRANCH = re.compile(r'^Tree/Branch')
RE_GIT_DESCRIBE = re.compile(r'^Git\s{1}describe')
RE_REPORT_SECTION = re.compile(r'^Full\s{1}Report')
RE_DECFONFIG_SECTION = re.compile(r'.*_defconfig$')


def _parse_boot_log(boot_log):
    """Parse a boot log file.

    The structure of the file makes so that this function will return a list
    of documents, one for each defconfig found in the boot log file. Each
    document will then contain a list of all the boards.

    :param boot_log: Path to the boot log file. No checks are performed on it.
    :return A list of boot documents.
    """

    LOG.info("Importing boot log %s", boot_log)

    created = datetime.fromtimestamp(
        os.stat(boot_log).st_mtime, tz=tz_util.utc
    )

    job = None
    kernel = None
    defconfig = None

    report_section = False
    defconf_section = False

    boot_docs = []
    boot_doc = None

    with open(boot_log) as read_boot:
        for line in read_boot:
            line = line.strip()

            if line and not report_section:
                if RE_TREE_BRANCH.match(line):
                    job = line.split(':')[1].strip()
                elif RE_GIT_DESCRIBE.match(line):
                    kernel = line.split(':')[1].strip()
                elif RE_REPORT_SECTION.match(line):
                    report_section = True
            else:
                if line and report_section and not defconf_section:
                    if RE_DECFONFIG_SECTION.match(line):
                        defconfig = line.strip()
                        defconf_section = True

                        doc_id = BootDocument.ID_FORMAT % (
                            {
                                'job': job,
                                'kernel': kernel,
                                'defconfig': defconfig
                            }
                        )
                        boot_doc = BootDocument(doc_id, job, kernel, defconfig)
                        boot_doc.created = created
                elif line and report_section and defconf_section:
                    if line.startswith('-'):
                        continue
                    else:
                        board, time, status, warnings = _parse_board_line(line)
                        boot_doc.boards = dict(
                            board=board,
                            time=time,
                            status=status,
                            warnings=warnings
                        )
                elif not line and report_section and defconf_section:
                    # Done parsing the report section for this defconfig.
                    boot_docs.append(boot_doc)
                    defconf_section = False

    return boot_docs


def _parse_board_line(line):
    """Very hackish way of parsing the board line.

    This methods highly depends on how the boot log is built. If that changes
    this can easily break.

    :param line: The line to parse.
    :return A tuple with board name, time taken to boot, the status, and the
        number of warnings.
    """
    warnings = 0

    values = line.split()
    board = values.pop(0)

    time_d = timedelta(
        minutes=float(values[0]), seconds=float(values[2]))

    time = datetime(
        1970, 1, 1,
        minute=time_d.seconds / 60,
        second=time_d.seconds % 60,
        microsecond=time_d.microseconds
    )

    values = values[4:]

    status = values.pop(0)
    if len(values) > 1:
        warnings = values[1].strip(')')

    return (board, time, status, warnings)


def _import_all(database, base_path=BASE_PATH):
    """Handy function to import all boot logs."""
    boot_docs = []

    for job_dir in os.listdir(base_path):
        job_dir = os.path.join(base_path, job_dir)

        if os.path.isdir(job_dir):
            LOG.info("Importing boot logs from %s", job_dir)
            boot_docs.extend(
                _parse_boot_log(boot_log) for boot_log in glob.iglob(
                    os.path.join(job_dir, BOOT_REPORT_PATTERN)
                )
                if os.path.isfile(boot_log)
            )

    return boot_docs

if __name__ == '__main__':
    connection = pymongo.MongoClient()
    database = connection[DB_NAME]

    all_docs = _import_all(database)
    for docs in all_docs:
        save(database, docs)

    connection.disconnect()
