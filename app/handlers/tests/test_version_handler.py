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

"""Test module for the JobHandler handler."""

import tornado

import urls

from handlers.tests.test_handler_base import TestHandlerBase


class TestVersionHandler(TestHandlerBase):

    def get_app(self):
        return tornado.web.Application([urls._VERSION_URL], **self.settings)

    def test_get(self):
        response = self.fetch("/version", method="GET")
        self.assertEqual(response.code, 200,)

    def test_post(self):
        response = self.fetch("/version", method="POST", body="")
        self.assertEqual(response.code, 501)

    def test_delete(self):
        response = self.fetch("/version", method="DELETE")
        self.assertEqual(response.code, 501)
