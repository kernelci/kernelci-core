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

import unittest

from mock import patch

from utils.docimport import (
    import_all,
)


class TestParseJob(unittest.TestCase):

    @patch("os.listdir")
    def test_import_all_simple(self, mock_os_listdir):
        mock_os_listdir.side_effect = [
            ['job'], ['kernel'], ['defconf'],
        ]

        docs = import_all()
        self.assertEqual(len(docs), 2)

    @patch("os.listdir")
    def test_import_all_complex(self, mock_os_listdir):
        mock_os_listdir.side_effect = [
            ['job1', 'job2'],
            ['kernel1', 'kernel2'],
            ['defconf1', 'defconf2'],
            ['defconf3,', 'defconf4'],
            ['kernel3'],
            ['defconf5']
        ]

        docs = import_all()
        self.assertEqual(len(docs), 8)

    @patch("os.listdir")
    def test_import_all_documents_created(self, mock_os_listdir):
        mock_os_listdir.side_effect = [
            ['job'], ['kernel'], ['defconf'],
        ]

        docs = import_all()
        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0].name, "job-kernel")
        self.assertEqual(docs[1].job_id, "job-kernel")
