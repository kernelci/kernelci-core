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

"""The Celery application."""

from __future__ import absolute_import

import ConfigParser
import celery
import celery.schedules
import kombu.serialization
import os

import taskqueue.celeryconfig as celeryconfig
import taskqueue.serializer as serializer

import utils


CELERY_CONFIG_FILE = "/etc/linaro/kernelci-celery.cfg"
CELERY_CONFIG_SECTION = "celery"
TASKS_LIST = [
    "taskqueue.tasks.bisect",
    "taskqueue.tasks.boot",
    "taskqueue.tasks.build",
    "taskqueue.tasks.common",
    "taskqueue.tasks.compare",
    "taskqueue.tasks.report",
    "taskqueue.tasks.stats",
    "taskqueue.tasks.test"
]

# Register the custom decoder/encoder for celery with the name "kjson".
# This is in all effect a JSON format, with some extensions.
kombu.serialization.register(
    "kjson",
    serializer.kernelci_json_encoder,
    serializer.kernelci_json_decoder,
    content_type="application/json",
    content_encoding="utf-8"
)

app = celery.Celery(
    "tasks",
    include=TASKS_LIST
)

app.config_from_object(celeryconfig)

# Periodic tasks to be executed.
CELERYBEAT_SCHEDULE = {
    "calculate-daily-stats": {
        "task": "calculate-daily-statistics",
        "schedule": celery.schedules.crontab(minute=1, hour=12)
    }
}

# The database connection parameters.
# Read from a config file from disk.
DB_OPTIONS = {}
if os.path.exists(CELERY_CONFIG_FILE):
    parser = ConfigParser.ConfigParser()
    try:
        parser.read([CELERY_CONFIG_FILE])
        if parser.has_section(CELERY_CONFIG_SECTION):

            if parser.has_option(CELERY_CONFIG_SECTION, "dbhost"):
                DB_OPTIONS["dbhost"] = parser.get(
                    CELERY_CONFIG_SECTION, "dbhost")
            else:
                DB_OPTIONS["dbhost"] = "localhost"

            if parser.has_option(CELERY_CONFIG_SECTION, "dbport"):
                DB_OPTIONS["dbport"] = parser.getint(
                    CELERY_CONFIG_SECTION, "dbport")
            else:
                DB_OPTIONS["dbport"] = 27017

            if parser.has_option(CELERY_CONFIG_SECTION, "dbpool"):
                DB_OPTIONS["dbpool"] = parser.getint(
                    CELERY_CONFIG_SECTION, "dbpool")
            else:
                DB_OPTIONS["dbpool"] = 100

            if parser.has_option(CELERY_CONFIG_SECTION, "dbuser"):
                DB_OPTIONS["dbuser"] = parser.getint(
                    CELERY_CONFIG_SECTION, "dbuser")

            if parser.has_option(CELERY_CONFIG_SECTION, "dbpassword"):
                DB_OPTIONS["dbpassword"] = parser.getint(
                    CELERY_CONFIG_SECTION, "dbpassword")
    except ConfigParser.ParsingError:
        utils.LOG.error("Error reading config file from disk")

app.conf.update(
    DB_OPTIONS=DB_OPTIONS,
    CELERYBEAT_SCHEDULE=CELERYBEAT_SCHEDULE
)


if __name__ == "__main__":
    app.start()
