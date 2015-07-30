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

import bson
import copy
import datetime

import handlers.response as hresponse
import models
import models.lab
import models.token
import utils.db
import utils.validator as validator


def _update_lab_token(old_lab, new_lab, database):
    """Update the token labs.

    Check if the new token specified and the old one are different and, if so:
    - expire the old token
    - update the new lab reference with the new lab token ID

    :param old_lab: The old lab document.
    :type old_lab: dict
    :param new_lab: The new lab document.
    :type new_lab: dict
    :param database: The database connection.
    :return A 2-tuple: 200 if OK, 404 or 500 is not OK; a list of errors
    or an empty list
    """
    errors = []
    ret_val = 200

    # The user passed new token is the actual token value, not its ID.
    new_token_doc = utils.db.find_one2(
        database[models.TOKEN_COLLECTION],
        {models.TOKEN_KEY: new_lab[models.TOKEN_KEY]})

    # In the lab got from the db, the token is stored as a reference, we have
    # its ID not its real value.
    old_token_doc = utils.db.find_one2(
        database[models.TOKEN_COLLECTION],
        {models.ID_KEY: old_lab[models.TOKEN_KEY]})

    if new_token_doc:
        # If the two tokens are different:
        # - update the new_lab reference to store the token ID,
        # - expire the old token.
        if old_token_doc:
            if new_token_doc[models.TOKEN_KEY] != \
                    old_token_doc[models.TOKEN_KEY]:
                new_lab[models.TOKEN_KEY] = new_token_doc[models.ID_KEY]

                ret_val = utils.db.find_and_update(
                    database[models.TOKEN_COLLECTION],
                    {models.ID_KEY: old_lab[models.TOKEN_KEY]},
                    {models.EXPIRED_KEY: True}
                )
                if ret_val != 200:
                    errors.append("Error disabling old lab token")
        else:
            # No old token? Force a reference update.
            new_lab[models.TOKEN_KEY] = new_token_doc[models.ID_KEY]
            errors.append("Old lab token value not found, updating to new one")
    else:
        ret_val = 400
        errors.append("New token specified not found, will not be updated")

    return ret_val, errors


def update_lab(doc_id, json_obj, valid_keys, database):
    """Update a lab document based on the provided values.

    :param doc_id: The ID of the lab document to update.
    ;type doc_id: str
    :param json_obj: The JSON object with the data to update.
    :type json_obj: dict
    :param valid_keys: The list of valid keys that should be in the JSON data.
    :type valid_keys: list
    :param database: The database connection.
    :return A HandlerResponse.
    """
    response = hresponse.HandlerResponse(200)
    response.reason = "Lab document updated"
    errors = []

    bson_doc_id = bson.objectid.ObjectId(doc_id)
    old_lab = utils.db.find_one2(
        database[models.LAB_COLLECTION],
        {models.ID_KEY: bson_doc_id})

    if old_lab:
        new_lab = copy.deepcopy(json_obj)

        for key, val in json_obj.iteritems():
            if key not in valid_keys:
                new_lab.pop(key)
                errors.append("Unrecognized key '%s' will be dropped" % key)
                continue

            if old_lab[key] == val:
                new_lab.pop(key)

        if new_lab:
            is_valid = True
            if models.CONTACT_KEY in new_lab.viewkeys():
                is_valid, reason = validator.is_valid_lab_contact_data(new_lab)
                new_contact = new_lab[models.CONTACT_KEY]

                # Update the old token email contact address.
                ret_val = utils.db.find_and_update(
                    database[models.TOKEN_COLLECTION],
                    {models.ID_KEY: old_lab[models.TOKEN_KEY]},
                    {models.EMAIL_KEY: new_contact[models.EMAIL_KEY]}
                )
                if ret_val != 200:
                    errors.append("Error updating token with new email")

            if is_valid:
                new_lab[models.UPDATED_KEY] = datetime.datetime.now(
                    tz=bson.tz_util.utc)

                if models.TOKEN_KEY in new_lab.viewkeys():
                    _, local_errors = _update_lab_token(
                        old_lab, new_lab, database)
                    errors.extend(local_errors)

                ret_val = utils.db.find_and_update(
                    database[models.LAB_COLLECTION],
                    {models.ID_KEY: bson_doc_id}, new_lab)

                if ret_val != 200:
                    response.status_code = ret_val
                    response.reason = "Error updating lab document"
            else:
                response.status_code = 400
                response.reason = reason
        else:
            response.reason = "No new data to update, lab not modified"
    else:
        response.status_code = 404
        response.reason = "Provided lab ID does not exists"

    response.errors = errors

    return response


def _get_or_create_token(lab_doc, database):
    """Search for the token or create a new one.

    If the new lab creation specified a token, search it and send back the its
    ID and its value. Otherwise, create a new one.

    :param lab_doc: The new lab document.
    :type lab_doc: models.lab.LabDocument
    :param database: The database connection.
    :return A 3-tuple: status code (200, 201 or 500); the token ID value as
    saved in the database; the token value.
    """
    ret_val = 200
    token_id = None
    token = None

    if lab_doc.token:
        token_doc = utils.db.find_one2(
            database[models.TOKEN_COLLECTION],
            {models.TOKEN_KEY: lab_doc.token})

        if token_doc:
            token_id = token_doc[models.ID_KEY]
            token = token_doc[models.TOKEN_KEY]
        else:
            ret_val = 500
    else:
        token_doc = models.token.Token()
        token_doc.email = lab_doc.contact[models.EMAIL_KEY]
        token_doc.is_post_token = True
        token_doc.is_delete_token = True
        token_doc.is_lab_token = True
        token = token_doc.token
        ret_val, token_id = utils.db.save(database, token_doc, manipulate=True)
        if ret_val == 500:
            token = None

    return ret_val, token_id, token


def create_lab(json_obj, database, request_uri):
    """Create a new lab document in the database.

    :param json_obj: The JSON object with the data to create the new lab.
    :type json_obj: dict
    :param database: The database connection.
    :return A HandlerResponse.
    """
    response = hresponse.HandlerResponse(201)
    lab_name = json_obj.get(models.NAME_KEY)

    prev_lab = utils.db.find_one2(
        database[models.LAB_COLLECTION], {models.NAME_KEY: lab_name})

    if prev_lab:
        response.status_code = 400
        response.reason = "Lab '%s' already exists" % lab_name
    else:
        lab_doc = models.lab.LabDocument.from_json(json_obj)
        lab_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)

        ret_val, token_id, token = _get_or_create_token(lab_doc, database)
        if all([ret_val != 200, ret_val != 201]):
            response.errors = \
                "Error saving or retrieving lab token: no token associated"

        lab_doc.token = token_id
        ret_val, lab_id = utils.db.save(database, lab_doc, manipulate=True)

        if ret_val == 201:
            response.result = {
                models.ID_KEY: lab_id,
                models.NAME_KEY: lab_name,
                models.TOKEN_KEY: token
            }
            response.headers = {"Location": request_uri + "/" + str(lab_id)}
        else:
            response.status_code = ret_val
            response.reason = "Error saving new lab '%s'" % lab_name

    return response
