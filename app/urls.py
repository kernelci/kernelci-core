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

"""Define URLs and handlers to server them."""

from tornado.web import url

import handlers.batch
import handlers.bisect
import handlers.boot
import handlers.count
import handlers.defconf
import handlers.job
import handlers.lab
import handlers.report
import handlers.subscription
import handlers.token
import handlers.version


_JOB_URL = url(
    r'/job(?P<sl>/)?(?P<id>.*)', handlers.job.JobHandler, name='job'
)
_DEFCONF_URL = url(
    r'/defconfig(?P<sl>/)?(?P<id>.*)',
    handlers.defconf.DefConfHandler,
    name='defconf'
)
_SUBSCRIPTION_URL = url(
    r'/subscription(?P<sl>/)?(?P<id>.*)',
    handlers.subscription.SubscriptionHandler,
    name='subscription',
)
_BOOT_URL = url(
    r'/boot(?P<sl>/)?(?P<id>.*)', handlers.boot.BootHandler, name='boot'
)
_COUNT_URL = url(
    r'/count(?P<sl>/)?(?P<id>.*)', handlers.count.CountHandler, name='count'
)
_TOKEN_URL = url(
    r'/token(?P<sl>/)?(?P<id>.*)', handlers.token.TokenHandler, name='token'
)
_BATCH_URL = url(
    r'/batch', handlers.batch.BatchHandler, name='batch'
)
_BISECT_URL = url(
    r"/bisect/(?P<collection>.*)/(?P<id>.*)",
    handlers.bisect.BisectHandler,
    name="bisect"
)
_LAB_URL = url(
    r"/lab(?P<sl>/)?(?P<id>.*)", handlers.lab.LabHandler, name="lab"
)
_VERSION_URL = url(
    r"/version", handlers.version.VersionHandler, name="version"
)
_REPORT_URL = url(
    r"/report[s]?(?P<sl>/)?(?P<id>.*)",
    handlers.report.ReportHandler,
    name="response"
)

APP_URLS = [
    _BATCH_URL,
    _BISECT_URL,
    _BOOT_URL,
    _COUNT_URL,
    _DEFCONF_URL,
    _JOB_URL,
    _LAB_URL,
    _SUBSCRIPTION_URL,
    _TOKEN_URL,
    _VERSION_URL,
    _REPORT_URL,
]
