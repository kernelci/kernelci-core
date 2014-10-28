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

from utils.bisect import _get_docs_until_pass


class BisectUtilsTest(unittest.TestCase):

    def test_get_docs_until_pass_no_pass(self):
        doc_list = [
            {"status": "foo", "id": 1},
            {"status": "foo", "id": 2},
            {"status": "foo", "id": 3},
            {"status": "foo", "id": 4},
            {"status": "foo", "id": 5},
        ]

        retrieved_list = [doc for doc in _get_docs_until_pass(doc_list)]
        self.assertListEqual(doc_list, retrieved_list)

    def test_get_docs_until_pass_with_pass_last(self):
        doc_list = [
            {"status": "foo", "id": 1},
            {"status": "foo", "id": 2},
            {"status": "foo", "id": 3},
            {"status": "foo", "id": 4},
            {"status": "PASS", "id": 5},
        ]

        retrieved_list = [doc for doc in _get_docs_until_pass(doc_list)]
        self.assertListEqual(doc_list, retrieved_list)

    def test_get_docs_until_pass_with_pass(self):
        doc_list = [
            {"status": "foo", "id": 1},
            {"status": "foo", "id": 2},
            {"status": "PASS", "id": 3},
            {"status": "foo", "id": 4},
            {"status": "foo", "id": 5},
        ]

        retrieved_list = [doc for doc in _get_docs_until_pass(doc_list)]
        self.assertEqual(len(retrieved_list), 3)
        self.assertListEqual(doc_list[:3], retrieved_list)
