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

"""All bisect related celery tasks."""

import taskqueue.celery as taskc
import utils.bisect.boot as bootb
import utils.bisect.defconfig as defconfigb


@taskc.app.task(name="import-boot-bisect")
def import_boot_bisect(data):
    """Just a wrapper around the real boot bisect import function.

    :param data: Bisection results from the JSON data.
    :type data: dictionary
    :return Status code with result of the operation.
    """
    return bootb.update_results(data, taskc.app.conf.db_options)


@taskc.app.task(name="boot-bisect", ignore_result=False)
def boot_bisect(doc_id, db_options, fields=None):
    """Run a boot bisect operation on the passed boot document id.

    :param doc_id: The boot document ID.
    :type doc_id: string
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dictionary
    :return The result of the boot bisect operation.
    """
    return bootb.execute_boot_bisection(doc_id, db_options, fields=fields)


@taskc.app.task(name="boot-bisect-compare-to", ignore_result=False)
def boot_bisect_compared_to(doc_id, compare_to, db_options, fields=None):
    """Run a boot bisect operation compared to the provided tree name.

    :param doc_id: The boot document ID.
    :type doc_id: string
    :param compare_to: The name of the tree to compare to.
    :type compare_to: string
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dictionary
    :return The result of the boot bisect operation.
    """
    return bootb.execute_boot_bisection_compared_to(
        doc_id, compare_to, db_options, fields=fields)


@taskc.app.task(name="build-bisect", ignore_result=False)
def defconfig_bisect(doc_id, db_options, fields=None):
    """Run a build bisect operation on the passed build document id.

    :param doc_id: The build document ID.
    :type doc_id: string
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dictionary
    :return The result of the build bisect operation.
    """
    return defconfigb.execute_build_bisection(
        doc_id, db_options, fields=fields)


@taskc.app.task(name="build-bisect-compared-to", ignore_result=False)
def defconfig_bisect_compared_to(doc_id, compare_to, db_options, fields=None):
    """Run a build bisect operation compared to the provided tree name.

    :param doc_id: The build document ID.
    :type doc_id: string
    :param compare_to: The name of the tree to compare to.
    :type compare_to: string
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dictionary
    :return The result of the build bisect operation.
    """
    return defconfigb.execute_build_bisection_compared_to(
        doc_id, compare_to, db_options, fields=fields)
