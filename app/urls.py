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
import handlers.count
import handlers.job
import handlers.lab
import handlers.report
import handlers.send
import handlers.stats
import handlers.test_case
import handlers.test_set
import handlers.test_suite
import handlers.token
import handlers.upload
import handlers.version


_JOB_URL = tornado.web.url(
    r"/job[s]?/?(?P<id>.*)", handlers.job.JobHandler, name="job")

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

_DEFCONF_URL = tornado.web.url(
    r"/defconfig[s]?/?$", handlers.build.BuildHandler, name="defconf")

_DEFCONF_ID_URL = tornado.web.url(
    r"/defconfig[s]?/(?P<id>[A-Za-z0-9]{24})/?$",
    handler=handlers.build.BuildHandler, name="defconfig-id")

_DEFCONFIG_ID_LOGS_URL = tornado.web.url(
    r"/defconfig[s]?/(?P<id>[A-Za-z0-9]{24})/logs/?$",
    handlers.build_logs.BuildLogsHandler, name="defconfig-id-logs")

_DEFCONFIG_LOGS_URL = tornado.web.url(
    r"/defconfig[s]?/logs/?$",
    handlers.build_logs.BuildLogsHandler, name="defconfig-logs")

_BOOT_URL = tornado.web.url(
    r"/boot[s]?/?(?P<id>.*)", handlers.boot.BootHandler, name="boot")

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

_TEST_SUITE_URL = tornado.web.url(
    r"/test[s]?/suite[s]?/?(?P<id>.*)",
    handlers.test_suite.TestSuiteHandler, name="test-suite")

_TEST_SET_URL = tornado.web.url(
    r"/test[s]?/set[s]?/?(?P<id>.*)",
    handlers.test_set.TestSetHandler, name="test-set")

_TEST_CASE_URL = tornado.web.url(
    r"/test[s]?/case[s]?/?(?P<id>.*)",
    handlers.test_case.TestCaseHandler, name="test-case")

_BOOT_TRIGGER_URL = tornado.web.url(
    r"/trigger/boot[s]?/?",
    handlers.boot_trigger.BootTriggerHandler, name="boot-trigger")

_STATS_URL = tornado.web.url(
    r"/statistics/?", handlers.stats.StatisticsHandler, name="statistics")

APP_URLS = [
    _BATCH_URL,
    _BISECT_URL,
    _BOOT_TRIGGER_URL,
    _BOOT_URL,
    _BUILD_ID_LOGS_URL,
    _BUILD_ID_URL,
    _BUILD_LOGS_URL,
    _BUILD_URL,
    _COUNT_URL,
    _DEFCONFIG_ID_LOGS_URL,
    _DEFCONFIG_LOGS_URL,
    _DEFCONF_ID_URL,
    _DEFCONF_URL,
    _JOB_URL,
    _LAB_URL,
    _REPORT_URL,
    _SEND_URL,
    _STATS_URL,
    _TEST_CASE_URL,
    _TEST_SET_URL,
    _TEST_SUITE_URL,
    _TOKEN_URL,
    _UPLOAD_URL,
    _VERSION_URL
]
