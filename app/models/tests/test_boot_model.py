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

import types
import unittest

from models.base import BaseDocument
from models.boot import BootDocument


class TestBootModel(unittest.TestCase):

    def test_boot_document_valid_instance(self):
        boot_doc = BootDocument('boot')
        self.assertIsInstance(boot_doc, BaseDocument)

    def test_boot_document_to_dict(self):
        boot_doc = BootDocument('boot')

        expected = {
            'kernel': None,
            'boards': [],
            'created': None,
            'defconfig': None,
            'job': None,
            '_id': 'boot',
        }

        self.assertEqual(expected, boot_doc.to_dict())

    def test_boot_document_to_json(self):
        boot_doc = BootDocument('boot')

        expected = (
            '{"kernel": null, "boards": [], "created": null, '
            '"defconfig": null, "job": null, "_id": "boot"}'
        )

        self.assertEqual(expected, boot_doc.to_json())

    def test_boot_document_boards(self):
        boot_doc = BootDocument('boot')
        boot_doc.boards = dict(board='board')

        self.assertIsInstance(boot_doc.boards, types.ListType)

    def test_boot_document_boards_with_list(self):
        boot_doc = BootDocument('boot')
        boot_doc.boards = dict(board='board')
        boot_doc.boards = [dict(board='board1')]

        self.assertIsInstance(boot_doc.boards, types.ListType)
        self.assertEqual(len(boot_doc.boards), 2)
