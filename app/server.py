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
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_unix_socket
from tornado.options import (
    define,
    options,
)
from tornado.web import Application
from uuid import uuid4

from handlers.app import AppHandler
from handlers.dbindexes import ensure_indexes
from urls import APP_URLS


DEFAULT_CONFIG_FILE = '/etc/linaro/kernelci-backend.cfg'

define('master_key', default=str(uuid4()), type=str, help="The master key")
define(
    'max_workers', default=20, type=int,
    help="The number of workers for the thread pool executor"
)
define('gzip', default=True)
define('debug', default=True)
define('autoreload', default=True)

# mongodb connection parameters.
define(
    'dbhost', default='localhost', type=str, help="The DB host to connect to"
)
define("dbport", default=27017, type=int, help="The DB port to connect to")
define(
    "dbuser", default="", type=str,
    help="The user name to use for the DB connection"
)
define(
    "dbpassword", default="", type=str,
    help="The password to use for the DB connection"
)
define("dbpool", default=250, type=int, help="The DB connections pool size")
define(
    "unixsocket", default=False, type=bool,
    help="If unix socket should be used"
)
define(
    "smtp_host", default='', type=str, help="The SMTP host to connect to")
define("smtp_user", default='', type=str, help="SMTP connection user")
define("smtp_password", default='', type=str, help="SMTP connection password")
define(
    "smtp_port", default=587, type=int,
    help="The SMTP connection port, default to 587")
define("smtp_sender", default='', type=str, help="The sender email address")
define(
    "send_delay", default=60*60+5, type=int,
    help="The delay in sending the report emails, "
         "default to 1 hour and 5 seconds"
)


class KernelCiBackend(Application):
    """The Kernel CI backend application.

    Where everything starts.
    """
    mongodb_client = None

    def __init__(self):

        db_options = {
            'dbhost': options.dbhost,
            'dbport': options.dbport,
            'dbuser': options.dbuser,
            'dbpassword': options.dbpassword,
            'dbpool': options.dbpool
        }

        mail_options = {
            "host": options.smtp_host,
            "user": options.smtp_user,
            "password": options.smtp_password,
            "port": options.smtp_port,
            "sender": options.smtp_sender
        }

        if self.mongodb_client is None:
            self.mongodb_client = pymongo.MongoClient(
                host=options.dbhost,
                port=options.dbport,
                max_pool_size=options.dbpool
            )

        settings = {
            'client': self.mongodb_client,
            'dboptions': db_options,
            "mailoptions": mail_options,
            'default_handler_class': AppHandler,
            'executor': ThreadPoolExecutor(max_workers=options.max_workers),
            'gzip': options.gzip,
            'debug': options.debug,
            'master_key': options.master_key,
            'autoreload': options.autoreload,
            "senddelay": options.send_delay
        }

        ensure_indexes(self.mongodb_client, db_options)

        super(KernelCiBackend, self).__init__(APP_URLS, **settings)


if __name__ == '__main__':
    if os.path.isfile(DEFAULT_CONFIG_FILE):
        options.parse_config_file(DEFAULT_CONFIG_FILE, final=False)

    options.parse_command_line()

    # Settings that should be passed also to the HTTPServer.
    HTTP_SETTINGS = {
        'xheaders': True,
    }

    if options.unixsocket:
        application = KernelCiBackend()

        server = HTTPServer(application, **HTTP_SETTINGS)
        unix_socket = bind_unix_socket("/tmp/kernelci-backend.socket")
        server.add_socket(unix_socket)
    else:
        KernelCiBackend().listen(8888, **HTTP_SETTINGS)

    tornado.ioloop.IOLoop.instance().start()
