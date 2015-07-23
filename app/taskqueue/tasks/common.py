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

"""General use celery tasks or functions."""

from __future__ import absolute_import

import celery

import taskqueue.celery as taskc
import utils.batch.common


@taskc.app.task(name="batch-executor", ignore_result=False)
def execute_batch(json_obj, db_options):
    """Run batch operations based on the passed JSON object.

    :param json_obj: The JSON object with the operations to perform.
    :type json_obj: dict
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return The result of the batch operations.
    """
    return utils.batch.common.execute_batch_operation(json_obj, db_options)


def run_batch_group(batch_op_list, db_options):
    """Execute a list of batch operations.

    :param batch_op_list: List of JSON object used to build the batch
    operation.
    :type batch_op_list: list
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return A list with all the results.
    """
    job = celery.group(
        execute_batch.s(batch_op, db_options)
        for batch_op in batch_op_list
    )
    result = job.apply_async()
    while not result.ready():
        pass
    # Use the result backend optimezed function to retrieve the results.
    # We are using redis.
    return result.join_native()
