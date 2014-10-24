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

from handlers.bisect import BisectHandler
from handlers.batch import BatchHandler
from handlers.boot import BootHandler
from handlers.count import CountHandler
from handlers.defconf import DefConfHandler
from handlers.job import JobHandler
from handlers.subscription import SubscriptionHandler
from handlers.token import TokenHandler


_JOB_URL = url(r'/api/job(?P<sl>/)?(?P<id>.*)', JobHandler, name='job')
_DEFCONF_URL = url(
    r'/api/defconfig(?P<sl>/)?(?P<id>.*)', DefConfHandler, name='defconf'
)
_SUBSCRIPTION_URL = url(
    r'/api/subscription(?P<sl>/)?(?P<id>.*)',
    SubscriptionHandler,
    name='subscription',
)
_BOOT_URL = url(r'/api/boot(?P<sl>/)?(?P<id>.*)', BootHandler, name='boot')
_COUNT_URL = url(
    r'/api/count(?P<sl>/)?(?P<id>.*)', CountHandler, name='count'
)
_TOKEN_URL = url(
    r'/api/token(?P<sl>/)?(?P<id>.*)', TokenHandler, name='token'
)
_BATCH_URL = url(
    r'/api/batch', BatchHandler, name='batch'
)
_BISECT_URL = url(
    r"/api/bisect/(?P<collection>.*)/(?P<id>.*)",
    BisectHandler,
    name="bisect"
)

APP_URLS = [
    _BATCH_URL,
    _BISECT_URL,
    _BOOT_URL,
    _COUNT_URL,
    _DEFCONF_URL,
    _JOB_URL,
    _SUBSCRIPTION_URL,
    _TOKEN_URL,
]
