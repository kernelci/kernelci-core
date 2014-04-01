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

"""Collection of utilities to handle subscriptions."""

import pymongo

from models import (
    DB_NAME,
    ID_KEY,
)
from models.job import JOB_COLLECTION
from models.subscription import (
    SUBSCRIPTION_COLLECTION,
    SubscriptionDocument,
)
from utils.db import (
    find_one,
    save,
)


def subscribe(json_obj, database):
    """Subscribe an email to a job.

    It accepts a dict-like object that should contain at least the `job_id' and
    `email' keys. All other keys will not be considered.

    At the moment no validation is run on the email provided.

    :param json_obj: A dict-like object with `job_id' and `email' fields.
    :param database: The database connection where to store the data.
    :return This function return 201 when the subscription has been performed,
            404 if the job to subscribe to does not exist, or 500 in case of
            an internal database error.
    """
    job = json_obj['job']
    emails = json_obj['email']

    job_doc = find_one(database[JOB_COLLECTION], job)
    if job_doc:
        job_id = job_doc[ID_KEY]
        subscription = find_one(
            database[SUBSCRIPTION_COLLECTION],
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

        return save(database, sub_obj)
    else:
        return 404


def send(job_id):
    """Send emails to the subscribers.

    :param job_id: The job ID for which to send notifications.
    :param database: The database where to search for subscribers.
    """
    database = pymongo.MongoClient()[DB_NAME]

    subscription = find_one(
        database[SUBSCRIPTION_COLLECTION], job_id, 'job_id'
    )

    if subscription:
        emails = subscription['emails']
