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

"""All callback related celery tasks."""

import taskqueue.celery as taskc
import utils
import utils.callback


@taskc.app.task(name="lava-boot")
def lava_boot(json_obj, lab_name):
    """Add boot data from a LAVA v2 job callback

    This is a wrapper around the actual function which runs in a Celery task.

    :param json_obj: The JSON object with the values necessary to import the
    LAVA boot data.
    :type json_obj: dictionary
    :param lab_name: The name of the LAVA lab that posted the callback.
    :type lab_name: string
    :return tuple The return code and the boot document id.
    """
    ret_code, doc_id, errors = \
        utils.callback.lava.add_boot(json_obj, lab_name,
                                     taskc.app.conf.db_options)
    # TODO: handle errors.
    return ret_code, doc_id
