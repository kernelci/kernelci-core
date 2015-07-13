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

"""Handler for the /lab URLs."""

import bson
import datetime
import urlparse

import handlers.base
import handlers.common as hcommon
import handlers.response as hresponse
import models
import models.lab as mlab
import models.token as mtoken
import utils.db
import utils.validator as validator


# pylint: disable=too-many-public-methods
class LabHandler(handlers.base.BaseHandler):
    """Handle all traffic through the /lab URLs."""

    def __init__(self, application, request, **kwargs):
        super(LabHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.LAB_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return models.LAB_VALID_KEYS.get(method, None)

    @staticmethod
    def _token_validation_func():
        return hcommon.valid_token_th

    def _post(self, *args, **kwargs):
        response = hresponse.HandlerResponse(201)

        json_obj = kwargs["json_obj"]

        valid_contact, reason = validator.is_valid_lab_contact_data(json_obj)
        if valid_contact:
            lab_id = kwargs.get("id", None)
            status_code, reason, result, headers = self._create_or_update(
                json_obj, lab_id)

            response.status_code = status_code
            response.result = result
            if reason:
                response.reason = reason
            if headers:
                response.headers = headers
        else:
            response.status_code = 400
            if reason:
                response.reason = reason

        return response

    def _create_or_update(self, json_obj, lab_id):
        """Create or update a new lab object.

        If the request comes in with a specified lab name, it will be treated
        as an update request.

        :param json_obj: The JSON data as sent in the request.
        :type json_obj: dict
        :param lab_id: The ID part of the request.
        :type lab_id: str
        :return A tuple with: status code, reason, result and headers.
        """
        status_code = None
        reason = None
        result = None
        headers = None
        old_lab = None
        name = json_obj.get(models.NAME_KEY)

        if lab_id:
            try:
                old_lab = utils.db.find_one(
                    self.collection,
                    [bson.objectid.ObjectId(lab_id)]
                )
            except bson.errors.InvalidId, ex:
                self.log.exception(ex)
                self.log.error("Wrong ID value '%s' passed as doc ID", lab_id)
                reason = "Wrong ID value provided"
        else:
            old_lab = utils.db.find_one(
                self.collection, [name], field=models.NAME_KEY
            )

        if all([lab_id, old_lab]):
            self.log.info(
                "Updating lab with ID '%s' from IP address %s",
                old_lab.get(models.ID_KEY), self.request.remote_ip
            )
            status_code, reason, result, headers = self._update_lab(
                json_obj, old_lab
            )
        elif all([lab_id, not old_lab]):
            status_code = 404
            reason = "Lab with name '%s' not found" % lab_id
        elif all([not old_lab, not lab_id]):
            self.log.info("Creating new lab object")
            status_code, reason, result, headers = self._create_new_lab(
                json_obj)
        else:
            status_code = 400
            if not reason:
                reason = (
                    "Lab with name '%s' already exists: did you mean to "
                    "update it?" % name
                )

        return status_code, reason, result, headers

    def _update_lab(self, json_obj, old_lab):
        """Update an existing lab object.

        :param json_obj: The JSON object with the lab data.
        :type json_obj: dict
        :param old_lab: The JSON object of the lab from the db.
        :type old_lab: dict
        :return A tuple with: status code, reason, result and headers.
        """
        status_code = None
        reason = None
        result = None
        headers = None

        # Locally used to store the contact information from the new lab
        # object.
        new_contact = None

        old_lab = mlab.LabDocument.from_json(old_lab)
        new_lab = mlab.LabDocument.from_json(json_obj)

        if new_lab.name:
            if old_lab.name != new_lab.name:
                # The is no setter for the name field in the Lab model.
                old_lab._name = new_lab.name

        if new_lab.contact:
            if old_lab.contact != new_lab.contact:
                old_lab.contact = new_lab.contact
                new_contact = new_lab.contact

        if new_lab.token:
            self._update_lab_token(old_lab, new_lab, new_contact)

        if new_lab.address:
            if old_lab.address != new_lab.address:
                old_lab.address = new_lab.address

        if old_lab.private != new_lab.private:
            old_lab.private = new_lab.private

        old_lab.updated_on = datetime.datetime.now(tz=bson.tz_util.utc)

        status_code, _ = utils.db.save(self.db, old_lab)
        if status_code != 201:
            reason = "Error updating lab '%s'" % old_lab.name
        else:
            reason = "Lab '%s' updated" % old_lab.name
            status_code = 200

        return status_code, reason, result, headers

    def _update_lab_token(self, old_lab, new_lab, new_contact):
        """Update references of lab token.

        :param old_lab: The lab object as found in the database.
        :type old_lab: LabDocument
        :param new_lab: The new lab object as passed by the user.
        :type new_lab: LabDocument
        :param new_contact: The contact information as found in the new lab
        document.
        :type new_contact: dict
        """
        # If the user specifies a new token, it will be doing so using the
        # actual token value, not its ID. We need to make sure we still
        # have the old token as defined in the old lab document, find the
        # new token and update accordingly using the token ID.
        old_token = utils.db.find_one(
            self.db[models.TOKEN_COLLECTION],
            [old_lab.token], field=models.TOKEN_KEY
        )
        new_token = utils.db.find_one(
            self.db[models.TOKEN_COLLECTION],
            [new_lab.token], field=models.TOKEN_KEY
        )

        if old_token:
            old_token = mtoken.Token.from_json(old_token)
        if new_token:
            new_token = mtoken.Token.from_json(new_token)

        if all([old_token, new_token]):
            # Both old and new tokens?
            # Expire the old one and save it.
            if old_token.token != new_token.token:
                old_lab.token = new_token.id

            old_token.expired = True
            ret_code, _ = utils.db.save(self.db, old_token)
            if ret_code != 201:
                self.log.warn("Error expiring old token '%s'", old_token.id)

        if all([old_token, not new_token, new_contact]):
            # Just the old token?
            # Make sure its contact information are correct and save it.
            old_token.username = (
                new_contact[models.NAME_KEY] +
                " " +
                new_contact[models.SURNAME_KEY]
            )
            old_token.email = new_contact[models.EMAIL_KEY]
            ret_code, _ = utils.db.save(self.db, old_token)
            if ret_code != 201:
                self.log.warn("Error updating old token '%s'", old_token.id)

    def _create_new_lab(self, json_obj):
        """Create a new lab in the database.

        :param json_obj: The JSON object with the lab data.
        :type json_obj: dict
        :return A tuple with: status code, reason, result and headers.
        """
        token_id = None
        ret_val = None
        reason = "New lab created"
        result = None
        headers = None

        lab_doc = mlab.LabDocument.from_json(json_obj)
        lab_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)

        if lab_doc.token:
            token_json = utils.db.find_one(
                self.db[models.TOKEN_COLLECTION],
                [lab_doc.token],
                field=models.TOKEN_KEY
            )
            if token_json:
                token = mtoken.Token.from_json(token_json)
                token_id = token.id
                ret_val = 200
            else:
                ret_val = 500
        else:
            token = mtoken.Token()
            token.email = lab_doc.contact[models.EMAIL_KEY]
            token.username = (
                lab_doc.contact[models.NAME_KEY] +
                " " +
                lab_doc.contact[models.SURNAME_KEY]
            )
            token.is_post_token = True
            token.is_delete_token = True
            token.is_lab_token = True
            ret_val, token_id = utils.db.save(self.db, token, manipulate=True)

        if ret_val == 201 or ret_val == 200:
            lab_doc.token = token_id
            ret_val, lab_id = utils.db.save(self.db, lab_doc, manipulate=True)
            if ret_val == 201:
                result = {
                    models.ID_KEY: lab_id,
                    models.NAME_KEY: lab_doc.name,
                    models.TOKEN_KEY: token.token
                }
                location = urlparse.urlunparse(
                    (
                        "http",
                        self.request.headers.get("Host"),
                        self.request.uri + "/" + lab_doc.name,
                        "", "", ""
                    )
                )
                headers = {"Location": location}
            else:
                reason = "Error saving new lab '%s'" % lab_doc.name
        else:
            reason = (
                "Error saving or finding the token for lab '%s'" % lab_doc.name
            )

        return (ret_val, reason, result, headers)

    def execute_delete(self, *args, **kwargs):
        # TODO: need to expire or delete token as well.
        response = None
        valid_token, _ = self.validate_req_token("DELETE")

        if valid_token:
            lab_id = kwargs.get("id", None)

            if lab_id:
                try:
                    lab_id = bson.objectid.ObjectId(lab_id)
                    if utils.db.find_one(self.collection, [lab_id]):
                        response = self._delete(lab_id)
                        if response.status_code == 200:
                            response.reason = "Resource '%s' deleted" % lab_id
                    else:
                        response = hresponse.HandlerResponse(404)
                        response.reason = "Resource '%s' not found" % lab_id
                except bson.errors.InvalidId, ex:
                    self.log.exception(ex)
                    self.log.error(
                        "Wrong ID value '%s' passed as doc ID", lab_id)
                    response = hresponse.HandlerResponse(400)
                    response.reason = "Wrong ID value provided"
            else:
                spec = hcommon.get_query_spec(
                    self.get_query_arguments, self._valid_keys("DELETE"))
                if spec:
                    response = self._delete(spec)
                    if response.status_code == 200:
                        response.reason = (
                            "Resources identified with '%s' deleted" % spec)
                else:
                    response = hresponse.HandlerResponse(400)
                    response.reason = (
                        "No valid data provided to execute a DELETE")
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

        return response

    def _delete(self, spec_or_id, **kwargs):
        response = hresponse.HandlerResponse(200)
        response.status_code = utils.db.delete(self.collection, spec_or_id)
        response.reason = self._get_status_message(response.status_code)

        return response
