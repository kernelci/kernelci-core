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

import tornado.web

from bson.json_util import dumps

from models import DB_NAME

ACCEPTED_MEDIA_TYPE = 'application/json'
ERROR_MESSAGES = {
    415: 'Please use "%s" as the default media type.' % (ACCEPTED_MEDIA_TYPE),
    400: 'Provided JSON is not valid.',
}


class BaseHandler(tornado.web.RequestHandler):

    @property
    def collection(self):
        return ''

    def get(self, *args, **kwargs):
        db = self.settings['client'][DB_NAME]

        if kwargs and kwargs['id']:
            result = db[self.collection].find_one(
                {
                    "_id": {"$in": [kwargs['id']]}
                }
            )
        else:
            result = db[self.collection].find()

        self.write(dumps(result))

    def write_error(self, status_code, **kwargs):
        if status_code in ERROR_MESSAGES.keys():
            self.finish(
                "<html><title>%(code)s: %(default_msg)s</title>"
                "<body>%(error_msg)s</body></html>" % {
                    "code": status_code,
                    "default_msg": self._reason,
                    "error_msg": ERROR_MESSAGES[status_code]
                }
            )
        else:
            super(BaseHandler, self).write_error(status_code)
