#!/usr/bin/env python
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

"""The Tornado application base module."""

import os
import pymongo
import tornado

from concurrent.futures import ThreadPoolExecutor
from tornado.options import (
    define,
    options,
)
from tornado.web import Application
from uuid import uuid4

from handlers.app import AppHandler
from urls import APP_URLS
from utils.dbindexes import ensure_indexes


DEFAULT_CONFIG_FILE = '/etc/linaro/kernelci-backend.cfg'

define('master_key', default=str(uuid4()), type=str, help="The master key")
define(
    'max_workers', default=20, type=int,
    help="The number of workers for the thread pool executor"
)
define('gzip', default=True)
define('debug', default=True)
define('autoreload', default=True)


class KernelCiBackend(Application):
    """The Kernel CI backend application.

    Where everything starts.
    """

    mongodb_client = pymongo.MongoClient()

    def __init__(self):

        settings = {
            'client': self.mongodb_client,
            'default_handler_class': AppHandler,
            'executor': ThreadPoolExecutor(max_workers=options.max_workers),
            'gzip': options.gzip,
            'debug': options.debug,
            'master_key': options.master_key,
            'autoreload': options.autoreload,
        }

        ensure_indexes(self.mongodb_client)

        super(KernelCiBackend, self).__init__(APP_URLS, **settings)


if __name__ == '__main__':
    if os.path.isfile(DEFAULT_CONFIG_FILE):
        options.parse_config_file(DEFAULT_CONFIG_FILE, final=False)

    options.parse_command_line()

    # Settings that should be passed also to the HTTPServer.
    http_settings = {
        'xheaders': True,
    }

    KernelCiBackend().listen(8888, **http_settings)
    tornado.ioloop.IOLoop.instance().start()
