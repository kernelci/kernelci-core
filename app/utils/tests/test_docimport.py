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

import datetime
import logging
import mock
import mongomock
import os
import tempfile
import types
import unittest

from bson import tz_util

import models.defconfig as moddf
import utils.docimport as docimport


class TestParseJob(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.db = mongomock.Database(mongomock.Connection(), 'kernel-ci')

    def tearDown(self):
        logging.disable(logging.NOTSET)

    @mock.patch("os.stat")
    @mock.patch("os.path.isdir")
    @mock.patch("os.listdir")
    def test_import_all_simple(self, mock_os_listdir, mock_isdir, mock_stat):
        mock_os_listdir.side_effect = [
            ['job'], ['kernel'], ['defconf'],
        ]
        mock_isdir.side_effect = [True, True, True, True]
        mock_stat.st_mtime.return_value = datetime.datetime.now(tz=tz_util.utc)

        docs = docimport._import_all(self.db)
        self.assertEqual(len(docs), 2)

    @mock.patch("os.stat")
    @mock.patch("os.path.isdir")
    @mock.patch("os.walk")
    @mock.patch("os.listdir")
    def test_import_all_complex(
            self, mock_os_listdir, mock_os_walk, mock_isdir, mock_stat):
        mock_os_listdir.side_effect = [
            ['job1', 'job2'],
            ['kernel1', 'kernel2'],
            ['defconf1', 'defconf2'],
            ['defconf3', 'defconf4'],
            ['kernel3'],
            ['defconf5']
        ]

        mock_isdir.side_effect = list((True,) * 13)
        mock_stat.st_mtime.return_value = datetime.datetime.now(tz=tz_util.utc)

        docs = docimport._import_all(self.db)
        self.assertEqual(len(docs), 8)

    @mock.patch("os.stat")
    @mock.patch("os.path.isdir")
    @mock.patch("os.listdir")
    def test_import_all_documents_created(
            self, mock_os_listdir, mock_isdir, mock_stat):
        mock_os_listdir.side_effect = [
            ['job'], ['kernel'], ['defconf'],
        ]

        mock_isdir.side_effect = list((True,) * 4)
        mock_stat.st_mtime.return_value = datetime.datetime.now(tz=tz_util.utc)

        docs = docimport._import_all(self.db)
        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0].name, "job-kernel")

    @mock.patch('pymongo.MongoClient')
    @mock.patch("utils.db.find_one")
    def test_import_and_save(
            self, mock_find, mocked_client=mongomock.Connection()):
        json_obj = dict(job='job', kernel='kernel')
        mock_find.return_value = None

        self.assertEqual(
            docimport.import_and_save_job(json_obj, {}), 'job-kernel'
        )

    @mock.patch('utils.db.find_one')
    def test_import_job_building(self, mock_find_one):
        mock_find_one.return_value = []
        database = mongomock.Connection()

        docs, job_id = docimport._import_job('job', 'kernel', database)

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].status, 'BUILD')

    @mock.patch('os.stat')
    @mock.patch('utils.db.find_one')
    @mock.patch('utils.docimport._traverse_defconf_dir')
    @mock.patch('os.listdir')
    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    def test_import_job_done(
            self, mock_isdir, mock_exists, mock_listdir, mock_traverse,
            mock_find_one, mock_stat):
        mock_isdir.return_value = True
        mock_exists.return_value = True
        mock_listdir.return_value = []
        mock_traverse.return_value = []
        mock_find_one.return_value = []
        mock_stat.st_mtime.return_value = datetime.datetime.now(tz=tz_util.utc)

        database = mongomock.Connection()

        docs, job_id = docimport._import_job('job', 'kernel', database)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].status, 'PASS')

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

        defconf_doc = mock.MagicMock()

        try:
            fake_meta = tempfile.NamedTemporaryFile(delete=False)
            with open(fake_meta.name, 'w') as w_file:
                w_file.write(meta_content)

            docimport._parse_build_metadata(fake_meta.name, defconf_doc)
        finally:
            os.unlink(fake_meta.name)

        self.assertIsInstance(defconf_doc.metadata, types.DictionaryType)
        self.assertEqual(None, defconf_doc.metadata['kconfig_fragments'])
        self.assertEqual('arm', defconf_doc.metadata['arch'])

    @mock.patch('utils.docimport._parse_build_metadata')
    @mock.patch('os.path.isfile')
    @mock.patch(
        'os.walk', new=mock.Mock(return_value=[('defconf-dir', [], [])]))
    @mock.patch('os.stat')
    def test_traverse_defconf_dir_json(
            self, mock_stat, mock_isfile, mock_parser):
        mock_stat.st_mtime.return_value = datetime.datetime.now(tz=tz_util.utc)
        mock_isfile.side_effect = [False, False, True]

        defconf_doc = docimport._traverse_defconf_dir(
            'job', 'kernel', 'kernel-dir', 'defconf-dir'
        )

        self.assertIsInstance(defconf_doc, moddf.DefconfigDocument)
        self.assertEqual(defconf_doc.status, 'UNKNOWN')
        mock_parser.assert_called_once_with(
            'defconf-dir/build.json', defconf_doc
        )

    @mock.patch('utils.docimport._parse_build_metadata')
    @mock.patch('os.path.isfile')
    @mock.patch(
        'os.walk', new=mock.Mock(return_value=[('defconf-dir', [], [])]))
    @mock.patch('os.stat')
    def test_traverse_defconf_dir_nornal(
            self, mock_stat, mock_isfile, mock_parser):
        mock_stat.st_mtime.return_value = datetime.datetime.now(tz=tz_util.utc)
        mock_isfile.side_effect = [False, False, False, True]

        defconf_doc = docimport._traverse_defconf_dir(
            'job', 'kernel', 'kernel-dir', 'defconf-dir'
        )

        self.assertIsInstance(defconf_doc, moddf.DefconfigDocument)
        self.assertEqual(defconf_doc.status, 'UNKNOWN')
        mock_parser.assert_called_once_with(
            'defconf-dir/build.meta', defconf_doc
        )
