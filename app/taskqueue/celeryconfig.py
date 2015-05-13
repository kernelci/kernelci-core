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

BROKER_URL = "redis://localhost"
BROKER_POOL_LIMIT = 20
BROKER_TRANSPORT_OPTIONS = {
    "visibility_timeout": 60*60*6,
    "fanout_prefix": True,
    "fanout_patterns": True
}
# Use custom json encoder.
CELERY_ACCEPT_CONTENT = ["kjson"]
CELERY_RESULT_SERIALIZER = "kjson"
CELERY_TASK_SERIALIZER = "kjson"
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_IGNORE_RESULT = True
CELERY_DISABLE_RATE_LIMITS = True
# Use a different DB than the redis default one.
CELERY_RESULT_BACKEND = "redis://localhost/1"
