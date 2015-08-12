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

import unittest

import models.base as mbase
import models.stats as mstats


class TestStatsModel(unittest.TestCase):

    def test_daily_stats_document_instance(self):
        daily_stats = mstats.DailyStats()
        self.assertIsInstance(daily_stats, mbase.BaseDocument)

    def test_daily_stats_collection_name(self):
        daily_stats = mstats.DailyStats()
        self.assertEqual("daily_stats", daily_stats.collection)

    def test_daily_stats_to_dict(self):
        daily_stats = mstats.DailyStats()
        daily_stats.created_on = "now"
        daily_stats.id = "stats-id"
        daily_stats.total_boots = 10
        daily_stats.total_builds = 100
        daily_stats.total_jobs = 1000
        daily_stats.version = "foo"
        daily_stats.start_date = "yesterday"

        expected = {
            "_id": "stats-id",
            "biweekly_total_boots": 0,
            "biweekly_total_builds": 0,
            "biweekly_total_jobs": 0,
            "biweekly_unique_archs": 0,
            "biweekly_unique_boards": 0,
            "biweekly_unique_kernels": 0,
            "biweekly_unique_machs": 0,
            "biweekly_unique_trees": 0,
            "biweekly_unique_defconfigs": 0,
            "created_on": "now",
            "daily_total_boots": 0,
            "daily_total_builds": 0,
            "daily_total_jobs": 0,
            "daily_unique_archs": 0,
            "daily_unique_boards": 0,
            "daily_unique_kernels": 0,
            "daily_unique_machs": 0,
            "daily_unique_trees": 0,
            "daily_unique_defconfigs": 0,
            "start_date": "yesterday",
            "total_boots": 10,
            "total_builds": 100,
            "total_jobs": 1000,
            "total_unique_archs": 0,
            "total_unique_boards": 0,
            "total_unique_kernels": 0,
            "total_unique_machs": 0,
            "total_unique_trees": 0,
            "total_unique_defconfigs": 0,
            "version": "foo",
            "weekly_total_boots": 0,
            "weekly_total_builds": 0,
            "weekly_total_jobs": 0,
            "weekly_unique_archs": 0,
            "weekly_unique_boards": 0,
            "weekly_unique_kernels": 0,
            "weekly_unique_machs": 0,
            "weekly_unique_trees": 0,
            "weekly_unique_defconfigs": 0,
        }

        self.assertDictEqual(expected, daily_stats.to_dict())

    def test_daily_stats_from_json(self):
        self.assertIsNone(mstats.DailyStats.from_json({}))
        self.assertIsNone(mstats.DailyStats.from_json(()))
        self.assertIsNone(mstats.DailyStats.from_json(""))
        self.assertIsNone(mstats.DailyStats.from_json([]))
