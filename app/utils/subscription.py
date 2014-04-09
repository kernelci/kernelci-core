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
    update,
)
from utils.log import get_log


log = get_log()


def subscribe(database, json_obj):
    """Subscribe an email to a job.

    It accepts a dict-like object that should contain at least the `job_id' and
    `email' keys. All other keys will not be considered.

    At the moment no validation is run on the email provided.

    :param database: The database where to store the data.
    :param json_obj: A dict-like object with `job_id' and `email' fields.
    :return This function return 201 when the subscription has been performed,
            404 if the job to subscribe to does not exist, or 500 in case of
            an internal database error.
    """
    ret_val = 404

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

        ret_val = save(database, sub_obj)

    return ret_val


def unsubscribe(collection, doc_id, email):
    """Unsubscribe an email from a job.

    :param collection: The collection where operation will be performed.
    :param doc_id: The job ID from which the email should be unsubscribed.
    :type str
    :param email: The email to unsubscribe.
    :type str
    :return 200 on success, 400 if there is an error removing an email, 500
            in case of a database error.
    """
    ret_val = 400

    subscription = find_one(collection, doc_id)

    if subscription:
        emails = subscription['emails']
        try:
            emails.remove(email)
            ret_val = update(
                collection, {'_id': doc_id}, {'emails': emails}
            )
        except ValueError, ex:
            log.error(
                "Error removing email address from subscription with "
                "'_id': %s" % (doc_id)
            )
            log.exception(str(ex))

    return ret_val


def send(job_id):
    """Send emails to the subscribers.

    :param job_id: The job ID for which to send notifications.
    """
    # TODO: add logic to make sure we can send the notifications.
    # We should store the job status.
    database = pymongo.MongoClient()[DB_NAME]

    subscription = find_one(
        database[SUBSCRIPTION_COLLECTION], job_id, 'job_id'
    )

    if subscription:
        emails = subscription['emails']
        log.info("Sending emails to: %s" % (str(emails)))
