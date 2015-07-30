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

import bson
import logging
import mock
import mongomock
import random
import string
import unittest

import handlers.common.lab
import handlers.response
import models.lab


class TestLabCommon(unittest.TestCase):

    def setUp(self):
        super(TestLabCommon, self).setUp()
        logging.disable(logging.CRITICAL)
        self.database = mongomock.Connection()["kernel-ci"]
        self.doc_id = "".join(
            [random.choice(string.digits) for x in xrange(24)])
        self.valid_keys = [
            "contact", "token", "address", "name", "private"
        ]

    def tearDown(self):
        super(TestLabCommon, self).tearDown()
        logging.disable(logging.NOTSET)

    @mock.patch("utils.db.find_one2")
    def test_update_lab_token_no_new_token(self, mock_find):
        mock_find.return_value = None
        new_lab = {
            "token": "new-token"
        }
        old_lab = {
            "token": "old-token"
        }

        ret_val, errors = handlers.common.lab._update_lab_token(
            old_lab, new_lab, self.database)

        self.assertEqual(400, ret_val)
        self.assertIsNotNone(errors)
        self.assertEqual(1, len(errors))

    @mock.patch("utils.db.find_and_update")
    @mock.patch("utils.db.find_one2")
    def test_update_lab_token_with_new_token(self, mock_find, mock_update):
        new_lab = {
            "token": "new-token"
        }
        old_lab = {
            "token": "old-token"
        }
        new_token = {
            "_id": "new-token-id",
            "token": "new-token"
        }
        old_token = {
            "_id": "old-token-id",
            "token": "old-token"
        }
        expected_new_lab = {
            "token": "new-token-id"
        }
        mock_find.side_effect = [new_token, old_token]
        mock_update.return_value = 200

        ret_val, errors = handlers.common.lab._update_lab_token(
            old_lab, new_lab, self.database)

        self.assertEqual(200, ret_val)
        self.assertListEqual([], errors)
        self.assertDictEqual(expected_new_lab, new_lab)

    @mock.patch("utils.db.find_and_update")
    @mock.patch("utils.db.find_one2")
    def test_update_lab_token_with_new_token_error_saving(
            self, mock_find, mock_update):
        new_lab = {
            "token": "new-token"
        }
        old_lab = {
            "token": "old-token"
        }
        new_token = {
            "_id": "new-token-id",
            "token": "new-token"
        }
        old_token = {
            "_id": "old-token-id",
            "token": "old-token"
        }
        expected_new_lab = {
            "token": "new-token-id"
        }
        mock_find.side_effect = [new_token, old_token]
        mock_update.return_value = 500

        ret_val, errors = handlers.common.lab._update_lab_token(
            old_lab, new_lab, self.database)

        self.assertEqual(500, ret_val)
        self.assertEqual(1, len(errors))
        self.assertDictEqual(expected_new_lab, new_lab)

    @mock.patch("utils.db.find_one2")
    def test_update_lab_token_with_new_token_same(self, mock_find):
        new_lab = {
            "token": "new-token"
        }
        old_lab = {
            "token": "old-token"
        }
        new_token = {
            "_id": "token-id",
            "token": "new-token"
        }
        old_token = {
            "_id": "token-id",
            "token": "new-token"
        }
        mock_find.side_effect = [new_token, old_token]

        ret_val, errors = handlers.common.lab._update_lab_token(
            old_lab, new_lab, self.database)

        self.assertEqual(200, ret_val)
        self.assertListEqual([], errors)

    @mock.patch("utils.db.find_one2")
    def test_update_lab_token_with_new_token_no_old(self, mock_find):
        new_lab = {
            "token": "new-token"
        }
        old_lab = {
            "token": "old-token"
        }
        new_token = {
            "_id": "new-token-id",
            "token": "new-token"
        }
        old_token = None
        expected_new_lab = {
            "token": "new-token-id"
        }
        mock_find.side_effect = [new_token, old_token]

        ret_val, errors = handlers.common.lab._update_lab_token(
            old_lab, new_lab, self.database)

        self.assertEqual(200, ret_val)
        self.assertEqual(1, len(errors))
        self.assertDictEqual(expected_new_lab, new_lab)

    @mock.patch("utils.db.find_one2")
    def test_update_lab_no_old_lab(self, mock_find):
        mock_find.return_value = None
        json_obj = {}

        response = handlers.common.lab.update_lab(
            self.doc_id, json_obj, self.valid_keys, self.database)

        self.assertIsInstance(response, handlers.response.HandlerResponse)
        self.assertEqual(404, response.status_code)

    @mock.patch("utils.db.find_and_update")
    @mock.patch("utils.db.find_one2")
    def test_update_lab_with_old_lab(self, mock_find, mock_update):
        json_obj = {
            "name": "new-lab-name"
        }
        old_lab = {
            "name": "lab-name",
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "email@example.net"
            },
            "token": "token-id"
        }
        mock_find.return_value = old_lab
        mock_update.return_value = 200

        response = handlers.common.lab.update_lab(
            self.doc_id, json_obj, self.valid_keys, self.database)

        self.assertIsInstance(response, handlers.response.HandlerResponse)
        self.assertEqual(200, response.status_code)

    @mock.patch("utils.db.find_and_update")
    @mock.patch("utils.db.find_one2")
    def test_update_lab_with_old_lab_new_contact(self, mock_find, mock_update):
        json_obj = {
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "new-email@example.net"
            }
        }
        old_lab = {
            "name": "lab-name",
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "email@example.net"
            },
            "token": "token-id"
        }
        mock_find.return_value = old_lab
        mock_update.return_value = 200

        response = handlers.common.lab.update_lab(
            self.doc_id, json_obj, self.valid_keys, self.database)

        self.assertIsInstance(response, handlers.response.HandlerResponse)
        self.assertEqual(200, response.status_code)
        self.assertListEqual([], response.errors)

    @mock.patch("utils.db.find_and_update")
    @mock.patch("utils.db.find_one2")
    def test_update_lab_with_old_lab_new_contact_error(
            self, mock_find, mock_update):
        json_obj = {
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "new-email@example.net"
            }
        }
        old_lab = {
            "name": "lab-name",
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "email@example.net"
            },
            "token": "token-id"
        }
        mock_find.return_value = old_lab
        mock_update.side_effect = [500, 200]

        response = handlers.common.lab.update_lab(
            self.doc_id, json_obj, self.valid_keys, self.database)

        self.assertIsInstance(response, handlers.response.HandlerResponse)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.errors))

    @mock.patch("utils.db.find_one2")
    def test_update_lab_with_same_data(self, mock_find):
        json_obj = {
            "name": "lab-name",
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "email@example.net"
            }
        }
        old_lab = {
            "name": "lab-name",
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "email@example.net"
            },
            "token": "token-id"
        }
        mock_find.return_value = old_lab

        response = handlers.common.lab.update_lab(
            self.doc_id, json_obj, self.valid_keys, self.database)

        self.assertIsInstance(response, handlers.response.HandlerResponse)
        self.assertEqual(200, response.status_code)

    @mock.patch("utils.db.find_and_update")
    @mock.patch("handlers.common.lab._update_lab_token")
    @mock.patch("utils.db.find_one2")
    def test_update_lab_with_new_token(
            self, mock_find, mock_token_update, mock_update):
        json_obj = {
            "token": "token-value"
        }
        old_lab = {
            "name": "lab-name",
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "email@example.net"
            },
            "token": "token-id"
        }
        mock_find.return_value = old_lab
        mock_token_update.return_value = ("a-value", [])
        mock_update.return_value = 200

        response = handlers.common.lab.update_lab(
            self.doc_id, json_obj, self.valid_keys, self.database)

        self.assertIsInstance(response, handlers.response.HandlerResponse)
        self.assertEqual(200, response.status_code)
        self.assertListEqual([], response.errors)

    @mock.patch("utils.db.find_and_update")
    @mock.patch("utils.db.find_one2")
    def test_update_lab_with_error_updating(self, mock_find, mock_update):
        json_obj = {
            "name": "new-lab-name"
        }
        old_lab = {
            "name": "lab-name",
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "email@example.net"
            },
            "token": "token-id"
        }
        mock_find.return_value = old_lab
        mock_update.return_value = 500

        response = handlers.common.lab.update_lab(
            self.doc_id, json_obj, self.valid_keys, self.database)

        self.assertIsInstance(response, handlers.response.HandlerResponse)
        self.assertEqual(500, response.status_code)
        self.assertListEqual([], response.errors)

    @mock.patch("utils.db.find_one2")
    def test_update_lab_with_wrong_contact_data(self, mock_find):
        json_obj = {
            "name": "lab-name",
            "contact": {
                "email": "email@example.net"
            }
        }
        old_lab = {
            "name": "lab-name",
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "email@example.net"
            },
            "token": "token-id"
        }
        mock_find.return_value = old_lab

        response = handlers.common.lab.update_lab(
            self.doc_id, json_obj, self.valid_keys, self.database)

        self.assertIsInstance(response, handlers.response.HandlerResponse)
        self.assertEqual(400, response.status_code)

    @mock.patch("utils.db.find_and_update")
    @mock.patch("utils.db.find_one2")
    def test_update_lab_with_wrong_keys(self, mock_find, mock_update):
        json_obj = {
            "name": "new-lab-name",
            "foo": "bar"
        }
        old_lab = {
            "name": "lab-name",
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "email@example.net"
            },
            "token": "token-id"
        }
        mock_find.return_value = old_lab
        mock_update.return_value = 200

        response = handlers.common.lab.update_lab(
            self.doc_id, json_obj, self.valid_keys, self.database)

        self.assertIsInstance(response, handlers.response.HandlerResponse)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.errors))

    @mock.patch("utils.db.save")
    def test_get_or_create_token_no_provided_token(self, mock_save):
        mock_save.return_value = (201, "token-id")
        lab_doc = models.lab.LabDocument("fake-lab")
        lab_doc.contact = {
            "name": "Ema",
            "surname": "Nymton",
            "email": "email@example.net"
        }

        ret_val, token_id, token = handlers.common.lab._get_or_create_token(
            lab_doc, self.database)

        self.assertEqual(201, ret_val)
        self.assertEqual("token-id", token_id)
        self.assertIsNotNone(token)

    @mock.patch("utils.db.save")
    def test_get_or_create_token_no_provided_token_error(self, mock_save):
        mock_save.return_value = (500, None)
        lab_doc = models.lab.LabDocument("fake-lab")
        lab_doc.contact = {
            "name": "Ema",
            "surname": "Nymton",
            "email": "email@example.net"
        }

        ret_val, token_id, token = handlers.common.lab._get_or_create_token(
            lab_doc, self.database)

        self.assertEqual(500, ret_val)
        self.assertEqual(None, token_id)
        self.assertIsNone(token)

    @mock.patch("utils.db.find_one2")
    def test_get_or_create_token_with_provided_token(self, mock_find):
        mock_find.return_value = {
            "_id": "token-id",
            "token": "token-value"
        }
        lab_doc = models.lab.LabDocument("fake-lab")
        lab_doc.token = "12345678901234567890"

        ret_val, token_id, token = handlers.common.lab._get_or_create_token(
            lab_doc, self.database)

        self.assertEqual(200, ret_val)
        self.assertEqual("token-id", token_id)
        self.assertIsNotNone(token)
        self.assertEqual("token-value", token)

    @mock.patch("utils.db.find_one2")
    def test_get_or_create_token_with_provided_token_not_found(
            self, mock_find):
        mock_find.return_value = None
        lab_doc = models.lab.LabDocument("fake-lab")
        lab_doc.token = "12345678901234567890"

        ret_val, token_id, token = handlers.common.lab._get_or_create_token(
            lab_doc, self.database)

        self.assertEqual(500, ret_val)
        self.assertIsNone(token_id)
        self.assertIsNone(token)

    @mock.patch("utils.db.find_one2")
    def test_create_lab_with_same_lab(self, mock_find):
        mock_find.return_value = {
            "name": "fake-lab"
        }
        json_obj = {
            "name": "fake-lab"
        }

        response = handlers.common.lab.create_lab(
            json_obj, self.database, "/lab")

        self.assertIsInstance(response, handlers.response.HandlerResponse)
        self.assertEqual(400, response.status_code)

    @mock.patch("utils.db.save")
    @mock.patch("handlers.common.lab._get_or_create_token")
    @mock.patch("utils.db.find_one2")
    def test_create_lab_new_lab(self, mock_find, mock_get_token, mock_save):
        lab_id = bson.objectid.ObjectId()

        mock_find.return_value = None
        mock_get_token.return_value = (200, "token-id", "token-value")
        mock_save.return_value = (201, lab_id)
        json_obj = {
            "name": "fake-lab",
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "email@example.net"
            }
        }

        expected_headers = {
            "Location": "/lab/" + str(lab_id)
        }
        expected_result = {
            "_id": lab_id,
            "name": "fake-lab",
            "token": "token-value"
        }

        response = handlers.common.lab.create_lab(
            json_obj, self.database, "/lab")

        self.assertIsInstance(response, handlers.response.HandlerResponse)
        self.assertEqual(201, response.status_code)
        self.assertListEqual([], response.errors)
        self.assertDictEqual(expected_headers, response.headers)
        self.assertDictEqual(expected_result, response.result[0])

    @mock.patch("utils.db.save")
    @mock.patch("handlers.common.lab._get_or_create_token")
    @mock.patch("utils.db.find_one2")
    def test_create_lab_new_lab_token_error(
            self, mock_find, mock_get_token, mock_save):
        mock_find.return_value = None
        mock_get_token.return_value = (500, None, None)
        mock_save.return_value = (201, "lab-id")
        json_obj = {
            "name": "fake-lab",
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "email@example.net"
            }
        }

        expected_headers = {
            "Location": "/lab/lab-id"
        }
        expected_result = {
            "_id": "lab-id",
            "name": "fake-lab",
            "token": None
        }

        response = handlers.common.lab.create_lab(
            json_obj, self.database, "/lab")

        self.assertIsInstance(response, handlers.response.HandlerResponse)
        self.assertEqual(201, response.status_code)
        self.assertEqual(1, len(response.errors))
        self.assertDictEqual(expected_headers, response.headers)
        self.assertDictEqual(expected_result, response.result[0])

    @mock.patch("utils.db.save")
    @mock.patch("handlers.common.lab._get_or_create_token")
    @mock.patch("utils.db.find_one2")
    def test_create_lab_new_lab_token_error_save_error(
            self, mock_find, mock_get_token, mock_save):
        mock_find.return_value = None
        mock_get_token.return_value = (500, None, None)
        mock_save.return_value = (500, None)
        json_obj = {
            "name": "fake-lab",
            "contact": {
                "name": "Ema",
                "surname": "Nymton",
                "email": "email@example.net"
            }
        }

        response = handlers.common.lab.create_lab(
            json_obj, self.database, "/lab")

        self.assertIsInstance(response, handlers.response.HandlerResponse)
        self.assertEqual(500, response.status_code)
        self.assertEqual(1, len(response.errors))
        self.assertIsNone(response.headers)
        self.assertIsNone(response.result)
