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
import unittest

import bson
import utils
import utils.errors


class TestBaseUtils(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_is_hidden(self):
        self.assertTrue(utils.is_hidden(".hidden"))
        self.assertFalse(utils.is_hidden("hidden"))

    def test_is_lab_dir(self):
        self.assertTrue(utils.is_lab_dir("lab-foo"))
        self.assertFalse(utils.is_lab_dir("foo"))

    def test_extrapolate_defconfig_full_non_valid(self):
        kconfig_fragments = "foo-CONFIG.bar"
        defconfig = "defconfig"

        self.assertEqual(
            defconfig,
            utils._extrapolate_defconfig_full_from_kconfig(
                kconfig_fragments, defconfig)
        )

    def test_extrapolate_defconfig_full_valid(self):
        kconfig_fragments = "frag-CONFIG=y.config"
        defconfig = "defconfig"

        expected = "defconfig+CONFIG=y"
        self.assertEqual(
            expected,
            utils._extrapolate_defconfig_full_from_kconfig(
                kconfig_fragments, defconfig)
        )

    def test_error_add_no_error(self):
        errors = {}
        expected = {}

        utils.errors.add_error(errors, None, None)
        self.assertDictEqual(expected, errors)

    def test_error_add_new_error(self):
        errors = {}
        expected = {500: ["Error message"]}

        utils.errors.add_error(errors, 500, "Error message")
        self.assertDictEqual(expected, errors)

    def test_error_add_another_error(self):
        errors = {
            500: ["First message"]
        }
        expected = {
            500: ["First message", "Second message"]
        }
        utils.errors.add_error(errors, 500, "Second message")
        self.assertDictEqual(expected, errors)

    def test_error_update_none(self):
        errors = {
            500: ["A message"]
        }
        expected = {
            500: ["A message"]
        }

        utils.errors.update_errors(errors, {})
        self.assertDictEqual(expected, errors)
        utils.errors.update_errors(errors, None)
        self.assertDictEqual(expected, errors)

    def test_error_update_new(self):
        errors = {}
        expected = {
            500: ["Updated message"]
        }

        utils.errors.update_errors(errors, {500: ["Updated message"]})
        self.assertDictEqual(expected, errors)

    def test_error_update_another(self):
        errors = {
            500: ["Old message"]
        }
        expected = {
            500: ["Old message", "New message"]
        }

        utils.errors.update_errors(errors, {500: ["New message"]})
        self.assertDictEqual(expected, errors)

    def test_valid_name(self):
        self.assertTrue(utils.valid_name("foo"))
        self.assertTrue(utils.valid_name("foo.bar"))
        self.assertTrue(utils.valid_name("foo+bar"))
        self.assertTrue(utils.valid_name("foo-bar"))
        self.assertTrue(utils.valid_name("foo_bar"))
        self.assertTrue(utils.valid_name("foo=bar"))

        self.assertFalse(utils.valid_name("foo*bar"))
        self.assertFalse(utils.valid_name("foo'bar"))
        self.assertFalse(utils.valid_name("foo\"bar"))
        self.assertFalse(utils.valid_name("foo~bar"))
        self.assertFalse(utils.valid_name("[foobar"))
        self.assertFalse(utils.valid_name("foobar]"))
        self.assertFalse(utils.valid_name("{foobar"))
        self.assertFalse(utils.valid_name("~foobar"))
        self.assertFalse(utils.valid_name("foobar~"))
        self.assertFalse(utils.valid_name("foo?bar"))
        self.assertFalse(utils.valid_name("foo/bar"))
        self.assertFalse(utils.valid_name(".foo/bar"))
        self.assertFalse(utils.valid_name("$foobar"))
        self.assertFalse(utils.valid_name("foo$bar"))

    def test_valid_test_name(self):
        self.assertTrue(utils.valid_test_name("a-test-name"))
        self.assertTrue(utils.valid_test_name("a_test_name"))
        self.assertTrue(utils.valid_test_name("a.test.name"))
        self.assertTrue(utils.valid_test_name("a+test+name"))

        self.assertFalse(utils.valid_test_name("a-test/name"))
        self.assertFalse(utils.valid_test_name("a-test=name"))
        self.assertFalse(utils.valid_test_name("a-test~name"))
        self.assertFalse(utils.valid_test_name("a-test\"name"))
        self.assertFalse(utils.valid_test_name("a-test'name"))
        self.assertFalse(utils.valid_test_name("+a+test+name"))
        self.assertFalse(utils.valid_test_name("a+test+name+"))
        self.assertFalse(utils.valid_test_name(".a.test.name"))
        self.assertFalse(utils.valid_test_name("a.test.name."))
        self.assertFalse(utils.valid_test_name("-a.test.name"))
        self.assertFalse(utils.valid_test_name("a.test.name-"))

    def test_update_id_fields(self):
        spec = {
            "job_id": "123344567",
            "_id": "0123456789ab0123456789ab",
            "foo": 1234,
            "build_id": "0123456789ab0123456789ab"
        }
        utils.update_id_fields(spec)
        expected = {
            "_id": bson.objectid.ObjectId("0123456789ab0123456789ab"),
            "foo": 1234,
            "build_id": bson.objectid.ObjectId("0123456789ab0123456789ab")
        }

        self.assertDictEqual(expected, spec)

    def test_clean_branch_name(self):
        self.assertIsNone(utils.clean_branch_name(None))
        self.assertEqual("", utils.clean_branch_name(""))
        self.assertEqual("master", utils.clean_branch_name("master"))
        self.assertEqual("master", utils.clean_branch_name("local/master"))
        self.assertEqual("for-next", utils.clean_branch_name("local/for-next"))
        self.assertEqual(
            "linux-4.4.y", utils.clean_branch_name("local/linux-4.4.y"))
