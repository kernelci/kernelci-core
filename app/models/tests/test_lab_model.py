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

import models.base as modb
import models.lab as modl


class TestLabModel(unittest.TestCase):

    def test_is_valid_base_class(self):
        self.assertIsInstance(modl.LabDocument(""), modb.BaseDocument)

    def test_model_collection(self):
        lab_doc = modl.LabDocument("")
        self.assertEqual(lab_doc.collection, "lab")

    def test_set_address_wrong_type(self):
        lab_doc = modl.LabDocument("foo")

        self.assertRaises(TypeError, setattr, lab_doc, "address", "")
        self.assertRaises(TypeError, setattr, lab_doc, "address", [])
        self.assertRaises(TypeError, setattr, lab_doc, "address", ())

    def test_set_contact_missing_valid_fields(self):
        lab_doc = modl.LabDocument("foo")

        self.assertRaises(ValueError, setattr, lab_doc, "contact", {})

    def test_set_contact_wrong_type(self):
        lab_doc = modl.LabDocument("foo")

        self.assertRaises(TypeError, setattr, lab_doc, "contact", "")
        self.assertRaises(TypeError, setattr, lab_doc, "contact", [])
        self.assertRaises(TypeError, setattr, lab_doc, "contact", ())

    def test_set_contact_missing_email(self):
        lab_doc = modl.LabDocument("foo")

        contact = {
            "name": "foo",
            "surname": "bar"
        }

        self.assertRaises(ValueError, setattr, lab_doc, "contact", contact)

    def test_set_contact_missing_name(self):
        lab_doc = modl.LabDocument("foo")

        contact = {
            "surname": "foo",
            "email": "bar"
        }

        self.assertRaises(ValueError, setattr, lab_doc, "contact", contact)

    def test_set_contact_missing_surname(self):
        lab_doc = modl.LabDocument("foo")

        contact = {
            "name": "foo",
            "email": "bar"
        }

        self.assertRaises(ValueError, setattr, lab_doc, "contact", contact)

    def test_set_contact_only_email(self):
        lab_doc = modl.LabDocument("foo")

        contact = {
            "email": "bar"
        }

        self.assertRaises(ValueError, setattr, lab_doc, "contact", contact)

    def test_set_contact_only_name(self):
        lab_doc = modl.LabDocument("foo")

        contact = {
            "name": "bar"
        }

        self.assertRaises(ValueError, setattr, lab_doc, "contact", contact)

    def test_set_contact_only_surname(self):
        lab_doc = modl.LabDocument("foo")

        contact = {
            "surname": "bar"
        }

        self.assertRaises(ValueError, setattr, lab_doc, "contact", contact)

    def test_lab_to_dict(self):
        lab_doc = modl.LabDocument("foo")
        lab_doc.created_on = "now"
        lab_doc.updated_on = "now"
        lab_doc.id = "bar"
        lab_doc.address = {
            "street_1": "a",
            "street_2": "b",
            "city": "c",
            "country": "d",
            "zipcode": "e",
            "longitude": "f",
            "latitude": "h"
        }
        lab_doc.private = True
        lab_doc.token = "token"
        lab_doc.contact = {
            "name": "foo",
            "surname": "bar",
            "telephone": "1234",
            "mobile": "1234",
            "email": "user@example.net"
        }

        expected = {
            "name": "foo",
            "created_on": "now",
            "updated_on": "now",
            "_id": "bar",
            "address": {
                "street_1": "a",
                "street_2": "b",
                "city": "c",
                "country": "d",
                "zipcode": "e",
                "longitude": "f",
                "latitude": "h"
            },
            "private": True,
            "token": "token",
            "contact": {
                "name": "foo",
                "surname": "bar",
                "telephone": "1234",
                "mobile": "1234",
                "email": "user@example.net"
            },
            "version": None,
        }

        self.assertDictEqual(expected, lab_doc.to_dict())

    def test_lab_from_json(self):
        json_obj = {
            "name": "foo",
            "created_on": "now",
            "updated_on": "now",
            "address": {
                "street_1": "a",
                "street_2": "b",
                "city": "c",
                "country": "d",
                "zipcode": "e",
                "longitude": "f",
                "latitude": "h"
            },
            "private": True,
            "token": "token",
            "contact": {
                "name": "foo",
                "surname": "bar",
                "telephone": "1234",
                "mobile": "1234",
                "email": "user@example.net"
            },
            "version": "1.0",
        }

        lab_doc = modl.LabDocument.from_json(json_obj)

        self.assertIsInstance(lab_doc, modb.BaseDocument)
        self.assertIsInstance(lab_doc, modl.LabDocument)
        self.assertDictEqual(lab_doc.to_dict(), json_obj)

    def test_lab_from_json_none(self):
        self.assertIsNone(modl.LabDocument.from_json(None))
        self.assertIsNone(modl.LabDocument.from_json({}))
