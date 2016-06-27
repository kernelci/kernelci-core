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
def import_boot(json_obj, db_options, mail_options):
    """Just a wrapper around the real boot import function.

    This is used to provide a Celery-task access to the import function.

    :param json_obj: The JSON object with the values necessary to import the
    boot report.
    :type json_obj: dictionary
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param mail_options: The options necessary to connect to the SMTP server.
    :type mail_options: dictionary
    :return tuple The return code; and the document id.
    """
    ret_code, doc_id, errors = \
        utils.boot.import_and_save_boot(json_obj, db_options)
    # TODO: handle errors.
    return ret_code, doc_id


@taskc.app.task(name="boot-regressions")
def find_regression(prev_res, db_options, mail_options):
    """Trigger the find regression function.

    This is a wrapper around the real function to provide a Celery task.
    This function is concataned to the `import_boot` one, and the results of
    the previous execution are injected here.

    :param prev_res: A list with the results of the previous task.
    :type prev_res: list
    :param db_options: The database connection parameters.
    :type db_options: dict
    :param mail_options: The email server connection parameters.
    :type mail_options: dict
    :return tuple The return code; and the document id.
    """
    ret_code = None
    doc_id = None

    if any([prev_res[0] == 201, prev_res[0] == 200]):
        ret_code, doc_id = utils.boot.regressions.find(prev_res[1], db_options)

    return ret_code, doc_id
