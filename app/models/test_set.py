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

"""The model that represent a test set document in the database."""

import copy
import types

import models
import models.base as mbase


# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes
class TestSetDocument(mbase.BaseDocument):
    """Model for a test set document.

    A test set is a container of test cases.
    """

    def __init__(self, name, test_suite_id, version):
        """

        :param name: The name given to this test set.
        :type name: string
        :param test_suite_id: The ID of the test set this test set
        belongs to.
        :type test_suite_id: string
        :param version: The version of the JSON schema of this test set.
        :type version: string
        """
        self._created_on = None
        self._id = None
        self._name = name
        self._version = version

        self._test_suite_id = test_suite_id

        self._test_case = []
        self._parameters = {}
        self._defects = []

        self.definition_uri = None
        self.metadata = {}
        self.time = -1
        self.vcs_commit = None

    @property
    def collection(self):
        return models.TEST_SET_COLLECTION

    @property
    def name(self):
        """The name of the test set."""
        return self._name

    @name.setter
    def name(self, value):
        """Set the name of the test set.

        :param value: The name of the test set.
        :type value: string
        """
        self._name = value

    @property
    def id(self):
        """The ID of the test set as registered in the database."""
        return self._id

    @id.setter
    def id(self, value):
        """Set the test set ID."""
        self._id = value

    @property
    def version(self):
        """The schema version of this test set."""
        return self._version

    @version.setter
    def version(self, value):
        """Set the schema version of this test set."""
        self._version = value

    @property
    def created_on(self):
        """The creation date of this test set."""
        return self._created_on

    @created_on.setter
    def created_on(self, value):
        """Set the creation date of this test set."""
        self._created_on = value

    @property
    def test_case(self):
        """The list of test cases performed by this test set."""
        return self._test_case

    @test_case.setter
    def test_case(self, value):
        """Set the list of test cases for this test set."""
        if not value:
            value = []
        if not isinstance(value, types.ListType):
            raise ValueError(
                "The associated test cases must be passed as a list")
        self._test_case = value

    @property
    def parameters(self):
        """The parameters that this test set ran with."""
        return self._parameters

    @parameters.setter
    def parameters(self, value):
        """Set the parameters this test set ran with.

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
    def test_suite_id(self):
        """The ID of the associated test suite."""
        return self._test_suite_id

    @test_suite_id.setter
    def test_suite_id(self, value):
        """Set the associated test suite ID.

        :param value: The test suite ID.
        :type value: string
        """
        self._test_suite_id = value

    @property
    def defects(self):
        """The defects associated with the test set."""
        return self._defects

    @defects.setter
    def defects(self, value):
        """Set the defect associated with the the test set.

        :param value: The defect object to add.
        :type value: dictionary
        """
        if value:
            if isinstance(value, types.ListType):
                self._defects.extend(value)
            else:
                self._defects.append(value)

    def to_dict(self):
        test_set = {
            models.CREATED_KEY: self.created_on,
            models.DEFECTS_KEY: self.defects,
            models.DEFINITION_URI_KEY: self.definition_uri,
            models.METADATA_KEY: self.metadata,
            models.NAME_KEY: self.name,
            models.PARAMETERS_KEY: self.parameters,
            models.TEST_CASE_KEY: self.test_case,
            models.TEST_SUITE_ID_KEY: self.test_suite_id,
            models.TIME_KEY: self.time,
            models.VCS_COMMIT_KEY: self.vcs_commit,
            models.VERSION_KEY: self.version
        }

        if self.id:
            test_set[models.ID_KEY] = self.id

        return test_set

    @staticmethod
    def from_json(json_obj):
        test_set = None
        if isinstance(json_obj, types.DictionaryType):
            local_obj = copy.deepcopy(json_obj)
            doc_pop = local_obj.pop

            set_id = doc_pop(models.ID_KEY, None)

            try:
                name = doc_pop(models.NAME_KEY)
                test_suite_id = doc_pop(models.TEST_SUITE_ID_KEY)
                version = doc_pop(models.VERSION_KEY)

                test_set = TestSetDocument(name, test_suite_id, version)
                test_set.id = set_id

                for key, val in local_obj.iteritems():
                    setattr(test_set, key, val)
            except KeyError:
                # Missing mandatory key? Return None.
                test_set = None

        return test_set
