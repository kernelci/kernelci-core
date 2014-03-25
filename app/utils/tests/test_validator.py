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

import json
import unittest

from utils.validator import (
    valid_json_job_put,
)


class JsonValidatorTest(unittest.TestCase):

    def test_valid_json_job_put_valid(self):
        json_string = '{"job": "job", "kernel": "kernel"}'

        self.assertTrue(valid_json_job_put(json.loads(json_string)))

    def test_valid_json_job_put_not_valid_job(self):
        json_string = '{"job": "job"}'

        self.assertFalse(valid_json_job_put(json.loads(json_string)))

    def test_valid_json_job_put_not_valid_kernel(self):
        json_string = '{"kernel": "kernel"}'

        self.assertFalse(valid_json_job_put(json.loads(json_string)))
