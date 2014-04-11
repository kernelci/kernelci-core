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

import logging
import mongomock
import os
import tempfile
import unittest

from types import DictionaryType
from mock import (
    MagicMock,
    patch,
)

from utils.docimport import (
    _import_all,
    _import_job,
    _parse_build_metadata,
    import_and_save,
)


class TestParseJob(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    @patch("os.listdir")
    def test_import_all_simple(self, mock_os_listdir):
        mock_os_listdir.side_effect = [
            ['job'], ['kernel'], ['defconf'],
        ]

        docs = _import_all()
        self.assertEqual(len(docs), 2)

    @patch("os.walk")
    @patch("os.listdir")
    def test_import_all_complex(self, mock_os_listdir, mock_os_walk):
        mock_os_listdir.side_effect = [
            ['job1', 'job2'],
            ['kernel1', 'kernel2'],
            ['defconf1', 'defconf2'],
            ['defconf3', 'defconf4'],
            ['kernel3'],
            ['defconf5']
        ]

        docs = _import_all()
        self.assertEqual(len(docs), 8)

    @patch("os.listdir")
    def test_import_all_documents_created(self, mock_os_listdir):
        mock_os_listdir.side_effect = [
            ['job'], ['kernel'], ['defconf'],
        ]

        docs = _import_all()
        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0].name, "job-kernel")
        self.assertEqual(docs[1].job_id, "job-kernel")

    @patch('pymongo.MongoClient')
    def test_import_and_save(self, mocked_client=mongomock.Connection()):
        json_obj = dict(job='job', kernel='kernel')

        self.assertEqual(import_and_save(json_obj), 'job-kernel')

    @patch('utils.docimport.find_one')
    def test_import_job_building(self, mock_find_one):
        mock_find_one.return_value = []
        database = mongomock.Connection()

        docs, job_id = _import_job('job', 'kernel', database)

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].status, 'BUILDING')

    @patch('utils.docimport.find_one')
    @patch('utils.docimport._traverse_defconf_dir')
    @patch('os.listdir')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_import_job_done(
            self, mock_isdir, mock_exists, mock_listdir, mock_traverse,
            mock_find_one):
        mock_isdir.return_value = True
        mock_exists.return_value = True
        mock_listdir.return_value = []
        mock_traverse.return_value = []
        mock_find_one.return_value = []

        database = mongomock.Connection()

        docs, job_id = _import_job('job', 'kernel', database)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].status, 'DONE')

    def test_parse_and_update_build_metadata(self):
        meta_content = (
            '''
# A comment.
arch: arm
git_url: git://git.example.org
git_branch: test/branch
git_describe: vfoo.bar
git_commit: 1234567890
defconfig: defoo_confbar
kconfig_fragments:
tree_name: foo_tree

kernel_image: zImage
kernel_config: kernel.config
dtb_dir: dtbs
modules_dir: foo/bar
'''
        )

        defconf_doc = MagicMock()

        try:
            fake_meta = tempfile.NamedTemporaryFile(delete=False)
            with open(fake_meta.name, 'w') as w_file:
                w_file.write(meta_content)

            _parse_build_metadata(fake_meta.name, defconf_doc)
        finally:
            os.unlink(fake_meta.name)

        self.assertIsInstance(defconf_doc.metadata, DictionaryType)
        self.assertNotIn('kconfig_fragments', defconf_doc.metadata.keys())
        self.assertEqual('arm', defconf_doc.metadata['arch'])
