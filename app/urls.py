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

from handlers import (
    BootHandler,
    DefConfHandler,
    JobHandler,
    SubscriptionHandler,
    CountHandler,
)

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
    r'/api/count(?P<sl>/)?(?P<collection>.*)', CountHandler, name='count'
)

APP_URLS = [
    _BOOT_URL,
    _COUNT_URL,
    _DEFCONF_URL,
    _JOB_URL,
    _SUBSCRIPTION_URL,
]
