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

"""The model that represent a test case document in the database."""

import copy
import types

import models
import models.base as mbase


# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes
class TestCaseDocument(mbase.BaseDocument):
    """Model for a test case document.

    A test case is the smallest unit of a test group: it is the actual test
    that is run and that reports a result.
    """

    def __init__(self, name, test_group_id=None, version="1.0", status="PASS"):
        """

        :param name: The name given to this test case.
        :type name: string
        :param test_group_id: The ID of the test group this test case
        belongs to.
        :type test_group_id: string
        :param version: The version of the JSON schema of this test case.
        :type version: string
        """
        self._created_on = None
        self._id = None
        self._name = name
        self._status = status
        self._test_group_id = test_group_id
        self._version = version

        self._attachments = []
        self._measurements = []
        self._parameters = {}

        self.index = None
        self.definition_uri = None
        self.kvm_guest = None
        self.maximum = None
        self.metadata = {}
        self.minimum = None
        self.samples = None
        self.samples_sqr_sum = None
        self.samples_sum = None
        self.test_group_name = None
        self.time = -1
        self.vcs_commit = None

    @property
    def collection(self):
        return models.TEST_CASE_COLLECTION

    @property
    def name(self):
        """The name of the test case."""
        return self._name

    @name.setter
    def name(self, value):
        """Set the name of the test case.

        :param value: The name of the test case.
        :type value: string
        """
        self._name = value

    @property
    def id(self):
        """The ID of the test case as registered in the database."""
        return self._id

    @id.setter
    def id(self, value):
        """Set the test case ID."""
        self._id = value

    @property
    def version(self):
        """The schema version of this test case."""
        return self._version

    @version.setter
    def version(self, value):
        """Set the schema version of this test case."""
        self._version = value

    @property
    def created_on(self):
        """The creation date of this test case."""
        return self._created_on

    @created_on.setter
    def created_on(self, value):
        """Set the creation date of this test case."""
        self._created_on = value

    @property
    def parameters(self):
        """The parameters that this test case ran with."""
        return self._parameters

    @parameters.setter
    def parameters(self, value):
        """Set the parameters this test case ran with.

        :param value: The parameters data structure.
        :type value: dict
        """
        if not value:
            value = {}
        if not isinstance(value, types.DictionaryType):
            raise ValueError(
                "The parameters must be passed as a dictionary")
        self._parameters = value

    @property
    def test_group_id(self):
        """The ID of the associated test group."""
        return self._test_group_id

    @test_group_id.setter
    def test_group_id(self, value):
        """Set the associated test group ID.

        :param value: The test group ID.
        :type value: string
        """
        self._test_group_id = value

    @property
    def attachments(self):
        """The attachments associated with this test case."""
        return self._attachments

    @attachments.setter
    def attachments(self, value):
        """Set the attachments associated with this test case.

        :param value: The attachments of this test case.
        :type value: list
        """
        if not value:
            value = []
        if not isinstance(value, types.ListType):
            raise ValueError("Attachments must be passed as a list")
        self._attachments = value

    def add_attachment(self, attachment):
        """Add (and append) an attachment to this test case.

        An attachment should be a non-empty dictionary like data structure.
        Empty values will not be stored in this data structure.

        :param attachment: The attachment to add.
        :type attachment: dict
        :raise ValueError if the passed value is not a dict.
        """
        if all([attachment, isinstance(attachment, types.DictType)]):
            self._attachments.append(attachment)
        else:
            raise ValueError(
                "Attachment must be non-empty dictionary-like object")

    @property
    def measurements(self):
        """The measurements registered by this test case."""
        return self._measurements

    @measurements.setter
    def measurements(self, value):
        """Set the measurements registered by this test case.

        :param value: The registered measurements.
        :type value: list
        """
        if not value:
            value = []
        if not isinstance(value, types.ListType):
            raise ValueError("Measurements must be passed as a list")
        self._measurements = value

    def add_measurement(self, measurement):
        """Add a single measurement to this test case.

        A measurement should be a non-empty dictionary-like data structure.
        Empty values will not be stored in this data structure. To register an
        empty result it is still necessary to provide a valid measurement data
        structure.

        :param measurement: The registered measurement.
        :type measurement: dict
        """
        if all([measurement, isinstance(measurement, types.DictionaryType)]):
            self._measurements.append(measurement)
        else:
            raise ValueError(
                "Measurement must be non-empty dictionary-like object")

    @property
    def status(self):
        """The status of this test case."""
        return self._status

    @status.setter
    def status(self, value):
        """Set the status of this test case.

        :param value: The status name.
        :type value: string
        """
        if all([value, value in models.VALID_TEST_CASE_STATUS]):
            self._status = value
        else:
            raise ValueError("Unsupported status value provided")

    def to_dict(self):
        test_case = {
            models.ATTACHMENTS_KEY: self.attachments,
            models.CREATED_KEY: self.created_on,
            models.DEFINITION_URI_KEY: self.definition_uri,
            models.KVM_GUEST_KEY: self.kvm_guest,
            models.INDEX_KEY: self.index,
            models.MAXIMUM_KEY: self.maximum,
            models.MEASUREMENTS_KEY: self.measurements,
            models.METADATA_KEY: self.metadata,
            models.MINIMUM_KEY: self.minimum,
            models.NAME_KEY: self.name,
            models.PARAMETERS_KEY: self.parameters,
            models.SAMPLES_KEY: self.samples,
            models.SAMPLES_SQUARE_SUM_KEY: self.samples_sqr_sum,
            models.SAMPLES_SUM_KEY: self.samples_sum,
            models.STATUS_KEY: self.status,
            models.TEST_GROUP_ID_KEY: self.test_group_id,
            models.TEST_GROUP_NAME_KEY: self.test_group_name,
            models.TIME_KEY: self.time,
            models.VCS_COMMIT_KEY: self.vcs_commit,
            models.VERSION_KEY: self.version
        }

        if self.id:
            test_case[models.ID_KEY] = self.id

        return test_case

    @staticmethod
    def from_json(json_obj):
        test_case = None
        if isinstance(json_obj, types.DictionaryType):
            local_obj = copy.deepcopy(json_obj)
            doc_pop = local_obj.pop

            set_id = doc_pop(models.ID_KEY, None)

            try:
                name = doc_pop(models.NAME_KEY)
                test_group_id = doc_pop(models.TEST_GROUP_ID_KEY)

                test_case = TestCaseDocument(name, test_group_id)
                test_case.id = set_id

                for key, val in local_obj.iteritems():
                    setattr(test_case, key, val)
            except KeyError:
                # Missing mandatory key? Return None.
                test_case = None

        return test_case
