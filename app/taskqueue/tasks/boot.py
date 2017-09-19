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

"""All boot related celery tasks."""

import taskqueue.celery as taskc
import utils.boot
import utils.boot.regressions


@taskc.app.task(name="import-boot")
def import_boot(json_obj):
    """Just a wrapper around the real boot import function.

    This is used to provide a Celery-task access to the import function.

    :param json_obj: The JSON object with the values necessary to import the
    boot report.
    :type json_obj: dictionary
    :return ObjectId The boot document object id.
    """
    return utils.boot.import_and_save_boot(json_obj, taskc.app.conf.db_options)


@taskc.app.task(name="boot-regressions")
def find_regression(boot_doc_id):
    """Trigger the find regression function.

    This is a wrapper around the real function to provide a Celery task.
    This function is concataned to the `import_boot` one, and the results of
    the previous execution are injected here.

    :param boot_doc_id: The boot document object id.
    :return ObjectId The boot object id.
    """
    utils.boot.regressions.find(boot_doc_id, taskc.app.conf.db_options)
    return boot_doc_id
