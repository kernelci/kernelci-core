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
import models.base as mbase


# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes
class TestSuiteDocument(mbase.BaseDocument):
    """Model for a test suite document.

    A test suite is a document that can store test cases and/or test sets ran.
    """

    def __init__(self, name, lab_name, defconfig_id, version):
        """The test suite document.

        :param name: The name given to this test suite.
        :type name: string
        :param lab_name: The name of the lab running this test suite.
        :type lab_name: string
        :param defconfig_id: The ID of the defconfig associated with this
        test suite.
        :type defconfig_id: string
        :param version: The version of the JSON schema of this test suite.
        :type version: string
        """
        self._created_on = None
        self._id = None
        self._name = name
        self._version = version

        self._defconfig_id = defconfig_id
        self._lab_name = lab_name

        self.arch = None
        self.board = None
        self.board_instance = None
        self.boot_id = None
        self.defconfig = None
        self.defconfig_full = None
        self.job = None
        self.job_id = None
        self.kernel = None
        self.metadata = {}
        self.test_case = []
        self.test_set = []
        self.time = -1

    @property
    def collection(self):
        return models.TEST_SUITE_COLLECTION

    @property
    def name(self):
        """The name of the test suite."""
        return self._name

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

    @property
    def defconfig_id(self):
        """The defconfig ID associated with this test suite."""
        return self._defconfig_id

    @defconfig_id.setter
    def defconfig_id(self, value):
        """Set the defconfig ID associated with this test suite."""
        self._defconfig_id = value

    @property
    def lab_name(self):
        """The lab name running this test suite."""
        return self._lab_name

    @lab_name.setter
    def lab_name(self, value):
        """Set the lab name running this test suite."""
        self._lab_name = value

    def to_dict(self):
        test_suite = {
            models.ARCHITECTURE_KEY: self.arch,
            models.BOARD_INSTANCE_KEY: self.board_instance,
            models.BOARD_KEY: self.board,
            models.BOOT_ID_KEY: self.boot_id,
            models.CREATED_KEY: self.created_on,
            models.DEFCONFIG_FULL_KEY: self.defconfig_full or self.defconfig,
            models.DEFCONFIG_ID_KEY: self.defconfig_id,
            models.DEFCONFIG_KEY: self.defconfig,
            models.JOB_ID_KEY: self.job_id,
            models.JOB_KEY: self.job,
            models.KERNEL_KEY: self.kernel,
            models.LAB_NAME_KEY: self.lab_name,
            models.METADATA_KEY: self.metadata,
            models.NAME_KEY: self.name,
            models.TEST_CASE_KEY: self.test_case,
            models.TEST_SET_KEY: self.test_set,
            models.TIME_KEY: self.time,
            models.VERSION_KEY: self.version,
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
                defconfig_id = doc_pop(models.DEFCONFIG_ID_KEY)
                version = doc_pop(models.VERSION_KEY)

                test_suite = TestSuiteDocument(
                    name, lab_name, defconfig_id, version)

                test_suite.id = suite_id

                for key, val in local_obj.iteritems():
                    setattr(test_suite, key, val)
            except KeyError:
                # Missing mandatory key? Return None.
                test_suite = None

        return test_suite
