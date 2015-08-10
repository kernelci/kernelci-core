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

"""Tasks to calculate statistics."""

import taskqueue.celery as taskc

import utils
import utils.db
import utils.stats.daily


@taskc.app.task(
    name="calculate-daily-statistics", ack_late=True, track_started=True)
def calculate_daily_statistics():
    db_options = taskc.app.conf.DB_OPTIONS
    daily_stats = utils.stats.daily.calculate_daily_stats(db_options)

    database = utils.db.get_db_connection(db_options)
    ret_val, doc_id = utils.db.save(database, daily_stats, manipulate=True)

    return ret_val, doc_id
