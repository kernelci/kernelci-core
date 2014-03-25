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

import pymongo
import tornado.ioloop
import tornado.web

from urls import app_urls


class KernelCiBackend(tornado.web.Application):
    def __init__(self, **overrides):
        client = pymongo.MongoClient()
        handlers = app_urls

        settings = {
            "client": client,
        }

        super(KernelCiBackend, self).__init__(handlers, **settings)


if __name__ == '__main__':
    application = KernelCiBackend()
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
