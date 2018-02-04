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

"""Test module for the TestSuiteHandler handler."""

import bson
import json
import mock
import tornado

import urls

from handlers.tests.test_handler_base import TestHandlerBase


class TestTestSuiteHandler(TestHandlerBase):

    def get_app(self):
        return tornado.web.Application([urls._TEST_SUITE_URL], **self.settings)

    @mock.patch("utils.db.find_and_count")
    def test_get(self, mock_find):
        mock_find.return_value = ([{"foo": "bar"}], 1)

        headers = {"Authorization": "foo"}
        response = self.fetch("/test/suite/", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("handlers.test_suite.TestSuiteHandler.collection")
    def test_get_by_id_not_found(self, collection, mock_id):
        mock_id.return_value = "suite-id"
        collection.find_one = mock.MagicMock()
        collection.find_one.return_value = None

        headers = {"Authorization": "foo"}
        response = self.fetch("/test/suite/suite-id", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("handlers.test_suite.TestSuiteHandler.collection")
    def test_get_by_id_not_found_empty_list(self, collection, mock_id):
        mock_id.return_value = "suite-id"
        collection.find_one = mock.MagicMock()
        collection.find_one.return_value = []

        headers = {"Authorization": "foo"}
        response = self.fetch("/test/suite/suite-id", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("handlers.test_suite.TestSuiteHandler.collection")
    def test_get_by_id_found(self, collection, mock_id):
        mock_id.return_value = "suite-id"
        collection.find_one = mock.MagicMock()
        collection.find_one.return_value = {"_id": "suite-id"}

        headers = {"Authorization": "foo"}
        response = self.fetch("/test/suite/suite-id", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_without_token(self):
        body = json.dumps(dict(name="suite", version="1.0"))

        response = self.fetch("/test/suite", method="POST", body=body)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_not_json_content(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        response = self.fetch(
            "/test/suite", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_wrong_content_type(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/suite", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_wrong_json(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(foo="foo", bar="bar"))

        response = self.fetch(
            "/test/suite", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("taskqueue.tasks.test.complete_test_suite_import")
    @mock.patch("handlers.test_suite.TestSuiteHandler._check_references")
    @mock.patch("utils.db.save")
    def test_post_correct(self, mock_save, mock_check, mock_task):
        mock_save.return_value = (201, "test-suite-id")
        mock_check.return_value = (200, None)
        mock_task.apply_async = mock.MagicMock()
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(
                name="test",
                lab_name="lab_name", version="1.0", build_id="build")
        )

        response = self.fetch(
            "/test/suite", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 201)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_correct_with_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="suite",
                version="1.0", lab_name="lab", build_id="build")
        )

        response = self.fetch(
            "/test/suite/fake-id", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("taskqueue.tasks.test.complete_test_suite_import")
    @mock.patch("handlers.test_suite.TestSuiteHandler._check_references")
    def test_post_correct_with_test_set(self, mock_check, mock_task):
        mock_check.return_value = (200, None)
        mock_task.apply_async = mock.MagicMock()
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="suite",
                version="1.0",
                lab_name="lab",
                build_id="build", test_set=[{"foo": "bar"}]
            )
        )

        response = self.fetch(
            "/test/suite", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("taskqueue.tasks.test.complete_test_suite_import")
    @mock.patch("handlers.test_suite.TestSuiteHandler._check_references")
    def test_post_correct_with_wrong_test_set(self, mock_check, mock_task):
        mock_check.return_value = (200, None)
        mock_task.apply_async = mock.MagicMock()
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="suite",
                version="1.0",
                lab_name="lab",
                build_id="build", test_set={"foo": "bar"}
            )
        )

        response = self.fetch(
            "/test/suite", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 201)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("taskqueue.tasks.test.complete_test_suite_import")
    @mock.patch("handlers.test_suite.TestSuiteHandler._check_references")
    def test_post_correct_with_test_case(self, mock_check, mock_task):
        mock_check.return_value = (200, None)
        mock_task.apply_async = mock.MagicMock()
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="suite",
                version="1.0",
                lab_name="lab",
                build_id="build", test_case=[{"foo": "bar"}]
            )
        )

        response = self.fetch(
            "/test/suite", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("taskqueue.tasks.test.complete_test_suite_import")
    @mock.patch("handlers.test_suite.TestSuiteHandler._check_references")
    def test_post_correct_with_wrong_test_case(self, mock_check, mock_task):
        mock_check.return_value = (200, None)
        mock_task.apply_async = mock.MagicMock()
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="suite",
                version="1.0",
                lab_name="lab",
                build_id="build", test_case={"foo": "bar"}
            )
        )

        response = self.fetch(
            "/test/suite", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 201)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("taskqueue.tasks.test.complete_test_suite_import")
    @mock.patch("handlers.test_suite.TestSuiteHandler._check_references")
    def test_post_correct_with_test_case_and_set(self, mock_check, mock_task):
        mock_check.return_value = (200, None)
        mock_task.apply_async = mock.MagicMock()
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="suite",
                version="1.0",
                lab_name="lab",
                build_id="build",
                test_case=[{"foo": "bar"}], test_set=[{"foo": "bar"}]
            )
        )

        response = self.fetch(
            "/test/suite", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("handlers.test_suite.TestSuiteHandler._check_references")
    @mock.patch("utils.db.save")
    def test_post_correct_with_error(self, mock_save, mock_check):
        mock_check.return_value = (200, None)
        mock_save.return_value = (500, None)
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test", lab_name="lab_name", version="1.0",
                build_id="build_id")
        )

        response = self.fetch(
            "/test/suite", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 500)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_correct_wrong_build_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test", lab_name="lab_name", version="1.0",
                build_id="build_id")
        )

        response = self.fetch(
            "/test/suite", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("bson.objectid.ObjectId")
    def test_post_correct_wrong_job_id(self, mock_oid):
        mock_oid.side_effect = ["build-id", bson.errors.InvalidId]
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test", lab_name="lab_name", version="1.0",
                build_id="build-id", job_id="job_id")
        )

        response = self.fetch(
            "/test/suite", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("bson.objectid.ObjectId")
    def test_post_correct_wrong_boot_id(self, mock_oid):
        mock_oid.side_effect = ["build-id", bson.errors.InvalidId]
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test", lab_name="lab_name", version="1.0",
                build_id="build-id", boot_id="boot_id")
        )

        response = self.fetch(
            "/test/suite", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.find_one2")
    def test_post_correct_defconfig_not_found(self, mock_find, mock_oid):
        mock_oid.side_effect = ["build-id", "boot-id"]
        mock_find.side_effect = [None, {"_id": "fake-boot"}]
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test", lab_name="lab_name", version="1.0",
                build_id="build-id", boot_id="boot_id")
        )

        response = self.fetch(
            "/test/suite", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.find_one2")
    def test_post_correct_job_not_found(self, mock_find, mock_oid):
        mock_oid.side_effect = ["build-id", "job-id"]
        mock_find.side_effect = [{"_id": "fake-id"}, None]
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test", lab_name="lab_name", version="1.0",
                build_id="build-id", job_id="job_id")
        )

        response = self.fetch(
            "/test/suite", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.find_one2")
    def test_post_correct_job_not_found2(self, mock_find, mock_oid):
        mock_oid.side_effect = ["build-id", "job-id", "boot-id"]
        mock_find.side_effect = [
            {"_id": "fake-id"}, None, {"_id": "fake-boot"}]
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test",
                lab_name="lab_name",
                version="1.0",
                build_id="build-id",
                job_id="job_id", boot_id="boot_id")
        )

        response = self.fetch(
            "/test/suite", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_no_token(self):
        response = self.fetch("/test/suite/id", method="PUT", body="")

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_wrong_token(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        self.validate_token.return_value = (False, None)

        response = self.fetch(
            "/test/suite/id", method="PUT", headers=headers, body="")

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_wrong_content_type(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/suite/id", method="PUT", body="", headers=headers)

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_no_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        response = self.fetch(
            "/test/suite/", method="PUT", headers=headers, body="")

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_no_valid_json(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(foo="foo", bar="bar"))

        response = self.fetch(
            "/test/suite/id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_no_json_data(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        response = self.fetch(
            "/test/suite/id", method="PUT", body="", headers=headers)

        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_no_valid_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(job="job", kernel="kernel"))

        response = self.fetch(
            "/test/suite/wrong-id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_put_id_not_found(self, mock_id, mock_find):
        mock_id.return_value = "fake-id"
        mock_find.return_value = None
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(job="job", kernel="kernel"))

        response = self.fetch(
            "/test/suite/wrong-id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.update")
    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_put_valid_no_error(self, mock_id, mock_find, mock_update):
        mock_id.return_value = "fake-id"
        mock_find.return_value = {"_id": "fake-id", "job": "bar"}
        mock_update.return_value = 200
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(job="job", kernel="kernel"))

        response = self.fetch(
            "/test/suite/fake-id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.update")
    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_put_valid_with_error(self, mock_id, mock_find, mock_update):
        mock_id.return_value = "fake-id"
        mock_find.return_value = {"_id": "fake-id", "job": "bar"}
        mock_update.return_value = 500
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(job="job", kernel="kernel"))

        response = self.fetch(
            "/test/suite/fake-id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 500)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete_no_token(self):
        response = self.fetch("/test/suite/id", method="DELETE")

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete_wrong_token(self):
        headers = {"Authorization": "foo"}
        self.validate_token.return_value = (False, None)

        response = self.fetch(
            "/test/suite/id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete_no_id(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/suite/", method="DELETE", headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete_wrong_id(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/suite/wrong-id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_delete_correct_not_found(self, mock_id, mock_find):
        mock_id.return_value = "fake-id"
        mock_find.return_value = None
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/suite/fake-id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.delete")
    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_delete_correct_with_error(self, mock_id, mock_find, mock_delete):
        mock_id.return_value = "fake-id"
        mock_find.return_value = {"_id": "fake-id"}
        mock_delete.return_value = 500
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/suite/fake-id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 500)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.delete")
    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_delete_correct(self, mock_id, mock_find, mock_delete):
        mock_id.return_value = "fake-id"
        mock_find.return_value = {"_id": "fake-id"}
        mock_delete.side_effect = [200, 500, 500]
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/suite/fake-id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
