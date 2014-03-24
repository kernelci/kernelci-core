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
from models.defconfig import DEFCONFIG_COLLECTION


class DefConfHandler(tornado.web.RequestHandler):

    def get(self, id=None):

        db = self.settings['client'][DB_NAME]
        defconfs = db[DEFCONFIG_COLLECTION].find()

        self.write(dumps(defconfs))
