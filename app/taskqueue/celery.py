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

import celery
import kombu.serialization
import os

import taskqueue.celeryconfig as celeryconfig
import taskqueue.serializer as serializer


TASKS_LIST = [
    "taskqueue.tasks.bisect",
    "taskqueue.tasks.boot",
    "taskqueue.tasks.build",
    "taskqueue.tasks.common",
    "taskqueue.tasks.report",
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

if os.environ.get("CELERY_CONFIG_MODULE", None):
    app.config_from_envar("CELERY_CONFIG_MODULE")


if __name__ == "__main__":
    app.start()
