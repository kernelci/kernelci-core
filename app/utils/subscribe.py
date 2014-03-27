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

from models import (
    JOB_COLLECTION,
    SUBSCRIPTION_COLLECTION,
)
from utils.db import find_one


def subscribe_emails(json_obj, db, callback):
    job = json_obj['job']
    emails = json_obj['emails']

    if not isinstance(emails, list):
        emails = list(emails)

    result = find_one(db[JOB_COLLECTION], job)
    if result:
        sub_id = None
        subscription = find_one(db[SUBSCRIPTION_COLLECTION])
        # Search for an already available subscription
        # If there is, update the list of emails, otherwise create new.
        # db[SUBSCRIPTION_COLLECTION].save()
    print result
    callback("DONE")
