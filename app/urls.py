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
    DefConfHandler,
    JobHandler,
    SubscriptionHandler
)

APP_URLS = [
    url(r'/api/defconfig(?P<sl>/)?(?P<id>.*)', DefConfHandler, name='defconf'),
    url(r'/api/job(?P<sl>/)?(?P<id>.*)', JobHandler, name='job'),
    url(r'/api/subscription', SubscriptionHandler, name='subscription')
]
