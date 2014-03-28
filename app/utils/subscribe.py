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

import types

from models import (
    JOB_COLLECTION,
    SUBSCRIPTION_COLLECTION,
    SubscriptionDocument,
)
from utils.db import (
    find_one,
    save,
)


def subscribe_email(json_obj, db, callback):
    """Subscribe an email to a job.

    It accepts a dict-like object that should contain at least the `job_id' and
    `email' keys. All other keys will not be considered.

    At the moment no validation is run on the email provided.

    :param json_obj: A dict-like object with `job_id' and `email' fields.
    :param db: The database connection where to store the data.
    :param callback: A function that will be called at the end.
    :return This function return 200 when the subscription has been performed,
            404 if the job to subscribe to does not exist, or 500 in case of
            an internal database error.
    """
    job = json_obj['job']
    emails = json_obj['email']

    if not isinstance(emails, types.ListType):
        # The subscription model store emails in a list, since we can have
        # more than one subscription.
        emails = [emails]

    job_doc = find_one(db[JOB_COLLECTION], job)
    if job_doc:
        job_id = job_doc['_id']
        subscription = find_one(
            db[SUBSCRIPTION_COLLECTION],
            job_id,
            'job_id'
        )

        if subscription:
            sub_obj = SubscriptionDocument.from_json(subscription)
            sub_obj.emails = emails
        else:
            sub_id = (
                SubscriptionDocument.SUBSCRIPTION_ID_FORMAT % (job_id)
            )
            sub_obj = SubscriptionDocument(sub_id, job_id, emails)

        callback(save(db[SUBSCRIPTION_COLLECTION], sub_obj))
    else:
        # Document not found.
        callback(404)
