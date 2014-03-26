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

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class BaseHandler(tornado.web.RequestHandler):

    @property
    def collection(self):
        return None

    @property
    def db(self):
        return self.settings['client'][DB_NAME]

    def get(self, *args, **kwargs):
        if kwargs and kwargs['id']:
            result = self.collection.find_one(
                {
                    "_id": {"$in": [kwargs['id']]}
                }
            )
        else:
            skip = int(self.get_query_argument('skip', default=0))
            limit = int(
                self.get_query_argument('limit', default=DEFAULT_LIMIT)
            )
            if limit > MAX_LIMIT:
                limit = MAX_LIMIT

            result = self.collection.find(limit=limit, skip=skip)

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
