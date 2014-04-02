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

"""The Celery application."""

from __future__ import absolute_import

import os

from celery import Celery


TASKS_LIST = ['taskqueue.tasks']


app = Celery(
    'tasks',
    include=TASKS_LIST
)

if os.environ.get('CELERY_CONFIG_MODULE', None):
    app.config_from_envar('CELERY_CONFIG_MODULE')
else:
    import taskqueue.celeryconfig as celeryconfig
    app.config_from_object(celeryconfig)


if __name__ == '__main__':
    app.start()
