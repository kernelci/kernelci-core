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

"""Define URLs and handlers to server them."""

import tornado.web

import handlers.batch
import handlers.bisect
import handlers.boot
import handlers.boot_trigger
import handlers.build
import handlers.build_logs
import handlers.compare
import handlers.count
import handlers.count_distinct
import handlers.distinct
import handlers.job
import handlers.boot_regressions
import handlers.job_logs
import handlers.lab
import handlers.report
import handlers.send
import handlers.stats
import handlers.test_case
import handlers.test_group
import handlers.token
import handlers.upload
import handlers.version
import handlers.callback


_JOB_URL = tornado.web.url(
    r"/job[s]?/?$", handlers.job.JobHandler, name="job")

_JOB_ID_URL = tornado.web.url(
    r"/job[s]?/(?P<id>[A-Za-z0-9]{24})/?$",
    handlers.job.JobHandler, name="job-id")

_JOB_ID_LOGS_URL = tornado.web.url(
    r"/job[s]?/(?P<id>[A-Za-z0-9]{24})/logs/?$",
    handlers.job_logs.JobLogsHandler, name="job-id-logs")

_JOB_LOGS_URL = tornado.web.url(
    r"/job[s]?/logs/?$",
    handlers.job_logs.JobLogsHandler, name="job-logs")

_JOB_DISTINCT_URL = tornado.web.url(
    r"/job[s]?/distinct/(?P<field>[A-Za-z0-9_]+)/?$",
    handlers.distinct.DistinctHandler,
    kwargs={"resource": "job"}, name="job-distinct"
)

_JOB_COMPARE_URL = tornado.web.url(
    r"/job[s]?/compare/?$",
    handlers.compare.CompareHandler,
    kwargs={"resource": "job"}, name="job-compare"
)

_JOB_COMPARE_ID_URL = tornado.web.url(
    r"/job[s]?/compare/(?P<id>[A-Za-z0-9]{24})/?$",
    handlers.compare.CompareHandler,
    kwargs={"resource": "job"}, name="job-compare-id"
)

_BUILD_URL = tornado.web.url(
    r"/build[s]?/?$", handlers.build.BuildHandler, name="build")

_BUILD_ID_URL = tornado.web.url(
    r"/build[s]?/(?P<id>[A-Za-z0-9]{24})/?$",
    handler=handlers.build.BuildHandler, name="build-id")

_BUILD_ID_LOGS_URL = tornado.web.url(
    r"/build[s]?/(?P<id>[A-Za-z0-9]{24})/logs/?$",
    handlers.build_logs.BuildLogsHandler, name="build-id-logs")

_BUILD_LOGS_URL = tornado.web.url(
    r"/build[s]?/logs/?$",
    handlers.build_logs.BuildLogsHandler, name="build-logs")

_BUILD_DISTINCT_URL = tornado.web.url(
    r"/build[s]?/distinct/(?P<field>[A-Za-z0-9_]+)/?$",
    handlers.distinct.DistinctHandler,
    kwargs={"resource": "build"}, name="build-distinct"
)

_BUILD_COMPARE_URL = tornado.web.url(
    r"/build[s]?/compare/?$",
    handlers.compare.CompareHandler,
    kwargs={"resource": "build"}, name="build-compare"
)

_BUILD_COMPARE_ID_URL = tornado.web.url(
    r"/build[s]?/compare/(?P<id>[A-Za-z0-9]{24})/?$",
    handlers.compare.CompareHandler,
    kwargs={"resource": "build"}, name="build-compare-id"
)

_BOOT_URL = tornado.web.url(
    r"/boot[s]?/?$", handlers.boot.BootHandler, name="boot")

_BOOT_ID_URL = tornado.web.url(
    r"/boot[s]?/(?P<id>[A-Za-z0-9]{24})/?$",
    handlers.boot.BootHandler, name="boot-id")

_BOOT_ID_REGRESSIONS_URL = tornado.web.url(
    r"/boot[s]?/(?P<id>[A-Za-z0-9]{24})/regressions/?$",
    handlers.boot_regressions.BootRegressionsHandler,
    name="boot-id-regressions")

_BOOT_REGRESSIONS_URL = tornado.web.url(
    r"/boot[s]?/regressions/?$",
    handlers.boot_regressions.BootRegressionsHandler,
    name="boot-regressions")

_BOOT_DISTINCT_URL = tornado.web.url(
    r"/boot[s]?/distinct/(?P<field>[A-Za-z0-9_]+)/?$",
    handlers.distinct.DistinctHandler,
    kwargs={"resource": "boot"}, name="boot-distinct"
)

_BOOT_COMPARE_URL = tornado.web.url(
    r"/boot[s]?/compare/?$",
    handlers.compare.CompareHandler,
    kwargs={"resource": "boot"}, name="boot-compare"
)

_BOOT_COMPARE_ID_URL = tornado.web.url(
    r"/boot[s]?/compare/(?P<id>[A-Za-z0-9]{24})/?$",
    handlers.compare.CompareHandler,
    kwargs={"resource": "boot"}, name="boot-compare-id"
)

_COUNT_URL = tornado.web.url(
    r"/count[s]?/?(?P<id>.*)", handlers.count.CountHandler, name="count")

_TOKEN_URL = tornado.web.url(
    r"/token[s]?/?(?P<id>.*)", handlers.token.TokenHandler, name="token")

_BATCH_URL = tornado.web.url(
    r"/batch", handlers.batch.BatchHandler, name="batch")

_BISECT_URL = tornado.web.url(
    r"/bisect[s]?/?(?P<id>.*)", handlers.bisect.BisectHandler, name="bisect")

_LAB_URL = tornado.web.url(
    r"/lab[s]?/?(?P<id>.*)", handlers.lab.LabHandler, name="lab")

_VERSION_URL = tornado.web.url(
    r"/version", handlers.version.VersionHandler, name="version")

_REPORT_URL = tornado.web.url(
    r"/report[s]?/?(?P<id>.*)", handlers.report.ReportHandler, name="response")

_UPLOAD_URL = tornado.web.url(
    r"/upload/?(?P<path>.*)", handlers.upload.UploadHandler, name="upload")

_SEND_URL = tornado.web.url(r"/send/?", handlers.send.SendHandler, name="send")

_TEST_GROUP_URL = tornado.web.url(
    r"/test[s]?/group[s]?/?(?P<id>.*)",
    handlers.test_group.TestGroupHandler, name="test-group"
)

_TEST_GROUP_DISTINCT_URL = tornado.web.url(
    r"/test[s]?/group[s]?/distinct/(?P<field>[A-Za-z0-9_]+)/?$",
    handlers.distinct.DistinctHandler,
    kwargs={"resource": "test_group"}, name="test-group-distinct"
)

_TEST_GROUP_COUNT_DISTINCT_URL = tornado.web.url(
    r"/test[s]?/group[s]?/count/distinct/(?P<field>[A-Za-z0-9_]+)/?$",
    handlers.count_distinct.CountDistinctHandler,
    kwargs={"resource": "test_group"}, name="test-group-count-distinct"
)

_TEST_CASE_URL = tornado.web.url(
    r"/test[s]?/case[s]?/?(?P<id>.*)",
    handlers.test_case.TestCaseHandler, name="test-case")

_TEST_CASE_DISTINCT_URL = tornado.web.url(
    r"/test[s]?/case[s]?/distinct/(?P<field>[A-Za-z0-9_]+)/?$",
    handlers.distinct.DistinctHandler,
    kwargs={"resource": "test_case"}, name="test-case-distinct"
)

_TEST_CASE_COUNT_DISTINCT_URL = tornado.web.url(
    r"/test[s]?/case[s]?/count/distinct/(?P<field>[A-Za-z0-9_]+)/?$",
    handlers.count_distinct.CountDistinctHandler,
    kwargs={"resource": "test_case"}, name="test-case-count-distinct"
)

_BOOT_TRIGGER_URL = tornado.web.url(
    r"/trigger/boot[s]?/?",
    handlers.boot_trigger.BootTriggerHandler, name="boot-trigger")

_STATS_URL = tornado.web.url(
    r"/statistics/?", handlers.stats.StatisticsHandler, name="statistics")

_LAVA_CALLBACK_URL = tornado.web.url(
    r"/callback/lava/(?P<action>[A-Za-z0-9_]+)",
    handlers.callback.LavaCallbackHandler, name="callback-lava"
)

APP_URLS = [
    _BATCH_URL,
    _BISECT_URL,
    _BOOT_COMPARE_ID_URL,
    _BOOT_COMPARE_URL,
    _BOOT_DISTINCT_URL,
    _BOOT_ID_REGRESSIONS_URL,
    _BOOT_ID_URL,
    _BOOT_REGRESSIONS_URL,
    _BOOT_TRIGGER_URL,
    _BOOT_URL,
    _BUILD_COMPARE_ID_URL,
    _BUILD_COMPARE_URL,
    _BUILD_DISTINCT_URL,
    _BUILD_ID_LOGS_URL,
    _BUILD_ID_URL,
    _BUILD_LOGS_URL,
    _BUILD_URL,
    _COUNT_URL,
    _JOB_COMPARE_ID_URL,
    _JOB_COMPARE_URL,
    _JOB_DISTINCT_URL,
    _JOB_ID_LOGS_URL,
    _JOB_ID_URL,
    _JOB_LOGS_URL,
    _JOB_URL,
    _LAB_URL,
    _LAVA_CALLBACK_URL,
    _REPORT_URL,
    _SEND_URL,
    _STATS_URL,
    _TEST_CASE_COUNT_DISTINCT_URL,
    _TEST_CASE_DISTINCT_URL,
    _TEST_CASE_URL,
    _TEST_GROUP_COUNT_DISTINCT_URL,
    _TEST_GROUP_DISTINCT_URL,
    _TEST_GROUP_URL,
    _TOKEN_URL,
    _UPLOAD_URL,
    _VERSION_URL
]
