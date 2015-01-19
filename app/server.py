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

import concurrent.futures
import os
import pymongo
import tornado
import tornado.httpserver
import tornado.netutil
import tornado.options as topt
import tornado.web
import uuid

import handlers.app as happ
import handlers.dbindexes as hdbindexes
import urls


DEFAULT_CONFIG_FILE = "/etc/linaro/kernelci-backend.cfg"

topt.define(
    "master_key", default=str(uuid.uuid4()), type=str, help="The master key")
topt.define(
    "max_workers", default=None, type=int,
    help="The number of workers for the thread pool executor"
)
topt.define("gzip", default=True)
topt.define("debug", default=True)
topt.define("autoreload", default=True)

# mongodb connection parameters.
topt.define(
    "dbhost", default="localhost", type=str, help="The DB host to connect to"
)
topt.define("dbport", default=27017, type=int, help="The DB port to connect to")
topt.define(
    "dbuser", default="", type=str,
    help="The user name to use for the DB connection"
)
topt.define(
    "dbpassword", default="", type=str,
    help="The password to use for the DB connection"
)
topt.define(
    "dbpool", default=250, type=int, help="The DB connections pool size")
topt.define(
    "unixsocket", default=False, type=bool,
    help="If unix socket should be used"
)
topt.define(
    "smtp_host", default="", type=str, help="The SMTP host to connect to")
topt.define("smtp_user", default="", type=str, help="SMTP connection user")
topt.define(
    "smtp_password", default="", type=str, help="SMTP connection password")
topt.define(
    "smtp_port", default=587, type=int,
    help="The SMTP connection port, default to 587")
topt.define(
    "smtp_sender", default="", type=str, help="The sender email address")
topt.define(
    "send_delay", default=60*60+5, type=int,
    help="The delay in sending the report emails, "
         "default to 1 hour and 5 seconds"
)
topt.define(
    "storage_url", default=None, type=str, help="The URL of the storage system")


class KernelCiBackend(tornado.web.Application):
    """The Kernel CI backend application.

    Where everything starts.
    """
    mongodb_client = None

    def __init__(self):

        db_options = {
            "dbhost": topt.options.dbhost,
            "dbport": topt.options.dbport,
            "dbuser": topt.options.dbuser,
            "dbpassword": topt.options.dbpassword,
            "dbpool": topt.options.dbpool
        }

        mail_options = {
            "host": topt.options.smtp_host,
            "user": topt.options.smtp_user,
            "password": topt.options.smtp_password,
            "port": topt.options.smtp_port,
            "sender": topt.options.smtp_sender
        }

        if self.mongodb_client is None:
            self.mongodb_client = pymongo.MongoClient(
                host=topt.options.dbhost,
                port=topt.options.dbport,
                max_pool_size=topt.options.dbpool
            )

        settings = {
            "client": self.mongodb_client,
            "dboptions": db_options,
            "mailoptions": mail_options,
            "default_handler_class": happ.AppHandler,
            "executor": concurrent.futures.ThreadPoolExecutor(
                max_workers=topt.options.max_workers),
            "gzip": topt.options.gzip,
            "debug": topt.options.debug,
            "master_key": topt.options.master_key,
            "autoreload": topt.options.autoreload,
            "senddelay": topt.options.send_delay,
            "storage_url": topt.options.storage_url
        }

        hdbindexes.ensure_indexes(self.mongodb_client, db_options)

        super(KernelCiBackend, self).__init__(urls.APP_URLS, **settings)


if __name__ == "__main__":
    if os.path.isfile(DEFAULT_CONFIG_FILE):
        topt.options.parse_config_file(DEFAULT_CONFIG_FILE, final=False)

    topt.options.parse_command_line()

    # Settings that should be passed also to the HTTPServer.
    HTTP_SETTINGS = {
        "xheaders": True,
    }

    if topt.options.unixsocket:
        application = KernelCiBackend()

        server = tornado.httpserver.HTTPServer(application, **HTTP_SETTINGS)
        unix_socket = tornado.netutil.bind_unix_socket(
            "/tmp/kernelci-backend.socket")
        server.add_socket(unix_socket)
    else:
        KernelCiBackend().listen(8888, **HTTP_SETTINGS)

    tornado.ioloop.IOLoop.instance().start()
