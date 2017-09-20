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
import tornado
import tornado.httpserver
import tornado.netutil
import tornado.options as topt
import tornado.web
import uuid

import handlers.app as happ
import handlers.dbindexes as hdbindexes
import urls
import utils.database.redisdb as redisdb
import utils.db


DEFAULT_CONFIG_FILE = "/etc/linaro/kernelci-backend.cfg"

topt.define(
    "master_key", default=str(uuid.uuid4()), type=str, help="The master key")
topt.define(
    "max_workers", default=5, type=int,
    help="The number of workers for the thread pool executor"
)
topt.define("gzip", default=True)
topt.define("debug", default=True)
topt.define("autoreload", default=True)
topt.define(
    "port", default=8888, type=int,
    help="The port number where the server should listen"
)

# mongodb connection parameters.
topt.define(
    "mongodb_host",
    default="localhost", type=str, help="The DB host to connect to")
topt.define(
    "mongodb_port", default=27017, type=int, help="The DB port to connect to")
topt.define(
    "mongodb_user",
    default="", type=str, help="The user name to use for the DB connection")
topt.define(
    "mongodb_password",
    default="", type=str, help="The password to use for the DB connection")
topt.define(
    "mongodb_pool", default=100, type=int, help="The DB connections pool size")

# redis connection parameters
topt.define(
    "redis_host",
    default="localhost",
    type=str, help="The Redis database host to connect to"
)
topt.define(
    "redis_port",
    default=6379, type=int, help="The Redis database port to connect to")
topt.define("redis_db", default=0, type=int, help="The Redis database to use")
topt.define(
    "redis_password", default="", type=str, help="The Redis database password")

# If we want to use UNIX socket for this server.
topt.define(
    "unixsocket",
    default=False, type=bool, help="If unix socket should be used")

# Email report delay in seconds
topt.define(
    "send_delay",
    default=60 * 60 + 5,
    type=int,
    help="The delay in sending the emails, default to 1 hour and 5 seconds"
)

# Storage
topt.define(
    "storage_url",
    default=None, type=str, help="The URL of the storage system")
topt.define(
    "buffer_size",
    default=1024 * 1024 * 500,
    type=int, help="The body buffer size for uploading files"
)


class KernelCiBackend(tornado.web.Application):
    """The Kernel CI backend application.

    Where everything starts.
    """
    database = None
    redis_con = None

    def __init__(self):

        db_options = {
            "mongodb_host": topt.options.mongodb_host,
            "mongodb_password": topt.options.mongodb_password,
            "mongodb_pool": topt.options.mongodb_pool,
            "mongodb_port": topt.options.mongodb_port,
            "mongodb_user": topt.options.mongodb_user,
            "redis_db": topt.options.redis_db,
            "redis_host": topt.options.redis_host,
            "redis_password": topt.options.redis_password,
            "redis_port": topt.options.redis_port
        }

        if not self.database:
            self.database = utils.db.get_db_connection(db_options)

        if not self.redis_con:
            self.redis_con = redisdb.get_db_connection(db_options)

        settings = {
            "database": self.database,
            "redis_connection": self.redis_con,
            "dboptions": db_options,
            "default_handler_class": happ.AppHandler,
            "executor": concurrent.futures.ThreadPoolExecutor(
                topt.options.max_workers),
            "gzip": topt.options.gzip,
            "debug": topt.options.debug,
            "master_key": topt.options.master_key,
            "autoreload": topt.options.autoreload,
            "senddelay": topt.options.send_delay,
            "storage_url": topt.options.storage_url,
            "max_buffer_size": topt.options.buffer_size
        }

        hdbindexes.ensure_indexes(self.database)

        super(KernelCiBackend, self).__init__(urls.APP_URLS, **settings)


if __name__ == "__main__":
    if os.path.isfile(DEFAULT_CONFIG_FILE):
        topt.options.parse_config_file(DEFAULT_CONFIG_FILE, final=False)

    topt.options.parse_command_line()

    # Settings that should be passed also to the HTTPServer.
    HTTP_SETTINGS = {
        "xheaders": True,
        "max_buffer_size": topt.options.buffer_size
    }

    if topt.options.unixsocket:
        application = KernelCiBackend()

        server = tornado.httpserver.HTTPServer(application, **HTTP_SETTINGS)
        unix_socket = tornado.netutil.bind_unix_socket(
            "/tmp/kernelci-backend.socket")
        server.add_socket(unix_socket)
    else:
        KernelCiBackend().listen(topt.options.port, **HTTP_SETTINGS)

    tornado.ioloop.IOLoop.instance().start()
