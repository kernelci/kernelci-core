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

import io
import logging
import mock
import os
import shutil
import tempfile
import types
import unittest

import utils.upload as upload


class TestUpload(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.temp_dir = tempfile.mkdtemp()
        self.this_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_dir = os.path.join(self.this_dir, "assets/")
        self.upload_file = os.path.join(self.assets_dir, "upload_file.txt")

    def tearDown(self):
        logging.disable(logging.NOTSET)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_is_valid_dir_path_valid(self):
        self.assertTrue(
            upload.is_valid_dir_path("foo-path", base_path=self.temp_dir))

    @mock.patch("os.path.isdir")
    @mock.patch("os.path.exists")
    def test_is_valid_dir_path_valid_2(self, mock_exists, mock_dir):
        mock_exists.return_value = True
        mock_dir.return_value = True
        self.assertTrue(
            upload.is_valid_dir_path("foo-path", base_path=self.temp_dir))

    @mock.patch("os.path.isdir")
    @mock.patch("os.path.exists")
    def test_is_valid_dir_path_not_valid(self, mock_exists, mock_dir):
        mock_exists.return_value = True
        mock_dir.return_value = False
        self.assertFalse(
            upload.is_valid_dir_path("foo-path", base_path=self.temp_dir))

    def test_file_exists_not(self):
        self.assertFalse(
            upload.file_exists("foo-file.txt", base_path=self.temp_dir))

    @mock.patch("os.path.isfile")
    def test_file_exists_yes(self, mock_file):
        mock_file.return_value = True
        self.assertTrue(
            upload.file_exists("foo-file.txt", base_path=self.temp_dir))

    def test_check_or_create_valid(self):
        ret_val, error = upload.check_or_create_upload_dir(
            "foo-dir", base_path=self.temp_dir)

        dest_path = os.path.join(self.temp_dir, "foo-dir")

        self.assertEqual(ret_val, 200)
        self.assertIsNone(error)
        self.assertTrue(os.path.exists(dest_path))
        self.assertTrue(os.path.isdir(dest_path))
        self.assertTrue(os.access(dest_path, os.R_OK | os.W_OK | os.X_OK))

    @mock.patch("os.access")
    @mock.patch("os.path.exists")
    def test_check_or_create_existing_valid(
            self, mock_exists, mock_access):
        mock_exists.return_value = True
        mock_access.return_value = True

        ret_val, error = upload.check_or_create_upload_dir(
            "foo-dir", base_path=self.temp_dir)

        self.assertEqual(ret_val, 200)
        self.assertIsNone(error)

    @mock.patch("os.access")
    @mock.patch("os.path.exists")
    def test_check_or_create_existing_not_valid(
            self, mock_exists, mock_access):
        mock_exists.return_value = True
        mock_access.return_value = False

        ret_val, error = upload.check_or_create_upload_dir(
            "foo-dir", base_path=self.temp_dir)

        self.assertEqual(ret_val, 500)
        self.assertIsNotNone(error)

    @mock.patch("os.makedirs")
    def test_check_or_create_non_existing_error(self, mock_make):
        mock_make.side_effect = OSError

        ret_val, error = upload.check_or_create_upload_dir(
            "foo-dir", base_path=self.temp_dir)

        self.assertEqual(ret_val, 500)
        self.assertIsNotNone(error)

    def test_create_or_update_simple(self):
        content = ""
        with io.open(self.upload_file, mode="rb") as f:
            content = f.read()

        path = ""
        filename = "foo-file.txt"
        content_type = None

        ret_dict = upload.create_or_update_file(
            path, filename, content_type, content, base_path=self.temp_dir)

        self.assertIsInstance(ret_dict, types.DictionaryType)
        self.assertEqual(ret_dict["status"], 201)
        self.assertEqual(ret_dict["filename"], filename)
        self.assertIsNone(ret_dict["error"])
        self.assertTrue(os.path.isfile(os.path.join(self.temp_dir, filename)))

    def test_create_or_update_subdir(self):
        content = ""
        with io.open(self.upload_file, mode="rb") as f:
            content = f.read()

        os.makedirs(os.path.join(self.temp_dir, "dest-path/"), mode=0775)

        path = "dest-path/"
        filename = "subdir/foo-file.txt"
        content_type = None

        subdir = os.path.join(self.temp_dir, path, "subdir/")
        file_path = os.path.join(subdir, "foo-file.txt")

        ret_dict = upload.create_or_update_file(
            path, filename, content_type, content, base_path=self.temp_dir)

        self.assertIsInstance(ret_dict, types.DictionaryType)
        self.assertEqual(ret_dict["status"], 201)
        self.assertEqual(ret_dict["filename"], filename)
        self.assertIsNone(ret_dict["error"])
        self.assertTrue(os.path.isdir(subdir))
        self.assertTrue(os.path.isfile(file_path))

    def test_create_or_update_with_error(self):
        content = ""
        with io.open(self.upload_file, mode="rb") as f:
            content = f.read()

        try:
            patch_open = mock.patch("io.open")
            mock_open = patch_open.start()
            mock_open.side_effect = IOError

            path = ""
            filename = "foo-file.txt"
            content_type = None

            ret_dict = upload.create_or_update_file(
                path, filename, content_type, content, base_path=self.temp_dir)

            self.assertIsInstance(ret_dict, types.DictionaryType)
            self.assertEqual(ret_dict["status"], 500)
            self.assertEqual(ret_dict["filename"], filename)
            self.assertIsNotNone(ret_dict["error"])
            self.assertFalse(
                os.path.isfile(os.path.join(self.temp_dir, filename)))
        finally:
            patch_open.stop()

    @mock.patch("utils.upload.check_or_create_upload_dir")
    def test_create_or_update_with_error_2(self, mock_check):
        mock_check.return_value = (500, "error")

        content = ""
        with io.open(self.upload_file, mode="rb") as f:
            content = f.read()

        path = "dest-path/"
        filename = "subdir/foo-file.txt"
        content_type = None

        subdir = os.path.join(self.temp_dir, path, "subdir/")
        file_path = os.path.join(subdir, "foo-file.txt")

        ret_dict = upload.create_or_update_file(
            path, filename, content_type, content, base_path=self.temp_dir)

        self.assertIsInstance(ret_dict, types.DictionaryType)
        self.assertEqual(ret_dict["status"], 500)
        self.assertEqual(ret_dict["filename"], filename)
        self.assertIsNotNone(ret_dict["error"])
        self.assertFalse(os.path.isdir(subdir))
        self.assertFalse(os.path.isfile(file_path))

    @mock.patch("os.path.exists")
    def test_create_or_update_file_already_exists(self, mock_check):
        mock_check.return_value = True

        content = ""
        with io.open(self.upload_file, mode="rb") as f:
            content = f.read()

        path = ""
        filename = "foo-file.txt"
        content_type = None

        ret_dict = upload.create_or_update_file(
            path, filename, content_type, content, base_path=self.temp_dir)

        self.assertIsInstance(ret_dict, types.DictionaryType)
        self.assertEqual(ret_dict["status"], 200)
        self.assertEqual(ret_dict["filename"], filename)
        self.assertIsNone(ret_dict["error"])
