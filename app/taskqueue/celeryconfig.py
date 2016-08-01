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

"""Celery configuration values."""

BROKER_URL = "redis://localhost/0"
BROKER_POOL_LIMIT = 250
BROKER_TRANSPORT_OPTIONS = {
    "visibility_timeout": 24000,
    "fanout_prefix": True,
    "fanout_patterns": True
}
CELERYD_PREFETCH_MULTIPLIER = 8
# Use custom json encoder.
CELERY_ACCEPT_CONTENT = ["kjson"]
CELERY_RESULT_SERIALIZER = "kjson"
CELERY_TASK_SERIALIZER = "kjson"
CELERY_TASK_RESULT_EXPIRES = 900
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_IGNORE_RESULT = False
CELERY_DISABLE_RATE_LIMITS = True
CELERY_RESULT_BACKEND = "redis://localhost/0"
CELERY_REDIS_MAX_CONNECTIONS = 250
# Custom log format.
CELERYD_LOG_FORMAT = '[%(levelname)8s/%(threadName)10s] %(message)s'
CELERYD_TASK_LOG_FORMAT = (
    '[%(levelname)8s/%(processName)10s] '
    '[%(task_name)s(%(task_id)s)] %(message)s'
)
