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

"""The model that represent a test suite document in the database."""

import copy
import types

import models
import models.base as modb


# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes
class TestSuiteDocument(modb.BaseDocument):
    """Model for a test suite document.

    A test suite is a document that can store test cases and/or test sets ran.
    """

    def __init__(self, name, lab_name, build_id=None, version="1.0"):
        """The test suite document.

        :param name: The name given to this test suite.
        :type name: string
        :param lab_name: The name of the lab running this test suite.
        :type lab_name: str
        :param build_id: The ID of the defconfig associated with this
        test suite.
        :type build_id: str
        :param version: The version of the JSON schema of this test suite.
        :type version: str
        """
        self._created_on = None
        self._id = None
        self._name = name
        self._version = version

        self.build_id = build_id
        self.lab_name = lab_name

        self.arch = None
        self.board = None
        self.board_instance = None
        self.defconfig = None
        self.defconfig_full = None
        self.definition_uri = None
        self.git_branch = None
        self.job = None
        self.job_id = None
        self.kernel = None
        self.metadata = {}
        self.test_case = []
        self.test_set = []
        self.time = -1
        self.vcs_commit = None

    @property
    def collection(self):
        return models.TEST_SUITE_COLLECTION

    @property
    def name(self):
        """The name of the test suite."""
        return self._name

    @name.setter
    def name(self, value):
        """Set the name of the test suite.

        :param value: The name of the test suite.
        :type value: string
        """
        self._name = value

    @property
    def id(self):
        """The ID of the test suite as registered in the database."""
        return self._id

    @id.setter
    def id(self, value):
        """Set the test suite ID."""
        self._id = value

    @property
    def version(self):
        """The schema version of this test suite."""
        return self._version

    @version.setter
    def version(self, value):
        """Set the schema version of this test suite."""
        self._version = value

    @property
    def created_on(self):
        """The creation date of this test suite."""
        return self._created_on

    @created_on.setter
    def created_on(self, value):
        """Set the creation date of this test suite."""
        self._created_on = value

    def to_dict(self):
        test_suite = {
            models.ARCHITECTURE_KEY: self.arch,
            models.BOARD_INSTANCE_KEY: self.board_instance,
            models.BOARD_KEY: self.board,
            models.BUILD_ID_KEY: self.build_id,
            models.CREATED_KEY: self.created_on,
            models.DEFCONFIG_FULL_KEY: self.defconfig_full or self.defconfig,
            models.DEFCONFIG_KEY: self.defconfig,
            models.DEFINITION_URI_KEY: self.definition_uri,
            models.GIT_BRANCH_KEY: self.git_branch,
            models.JOB_ID_KEY: self.job_id,
            models.JOB_KEY: self.job,
            models.KERNEL_KEY: self.kernel,
            models.LAB_NAME_KEY: self.lab_name,
            models.METADATA_KEY: self.metadata,
            models.NAME_KEY: self.name,
            models.TEST_CASE_KEY: self.test_case,
            models.TEST_SET_KEY: self.test_set,
            models.TIME_KEY: self.time,
            models.VCS_COMMIT_KEY: self.vcs_commit,
            models.VERSION_KEY: self.version
        }

        if self.id:
            test_suite[models.ID_KEY] = self.id

        return test_suite

    @staticmethod
    def from_json(json_obj):
        test_suite = None
        if isinstance(json_obj, types.DictionaryType):
            local_obj = copy.deepcopy(json_obj)
            doc_pop = local_obj.pop

            suite_id = doc_pop(models.ID_KEY, None)

            try:
                name = doc_pop(models.NAME_KEY)
                lab_name = doc_pop(models.LAB_NAME_KEY)
                build_id = doc_pop(models.BUILD_ID_KEY)

                test_suite = TestSuiteDocument(name, lab_name, build_id)
                test_suite.id = suite_id

                for key, val in local_obj.iteritems():
                    setattr(test_suite, key, val)
            except KeyError:
                # Missing mandatory key? Return None.
                test_suite = None

        return test_suite
