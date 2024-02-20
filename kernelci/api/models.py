# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2021-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

# Disable below flag as some models are just for storing the data and do not
# need methods
# pylint: disable=too-few-public-methods

# pylint: disable=no-name-in-module

"""KernelCI API model definitions used by client-facing endpoints"""

from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, ClassVar
import enum
from operator import attrgetter
import json
from bson import ObjectId
from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    BaseModel,
    Field,
    FileUrl,
    StrictInt,
)
from .models_base import (
    PyObjectId,
    DatabaseModel,
)


class StateValues(str, enum.Enum):
    """Enumeration to declare values to be used for Node.state"""

    RUNNING = 'running'
    AVAILABLE = 'available'
    CLOSING = 'closing'
    DONE = 'done'


class ResultValues(str, enum.Enum):
    """Enumeration to declare values to be used for Node.result"""

    PASS = 'pass'
    FAIL = 'fail'
    SKIP = 'skip'
    INCOMPLETE = 'incomplete'


class ErrorCodes(str, enum.Enum):
    """Enumeration to declare values to be used for Node.error_code.
    error_code mostly set if infrastructure error occurs (runtime internal
    error, scheduler error, etc.). This error code might be used not only
    for debugging and logging, but also for taking automated decisions, for
    example, to retry scheduling the job if runtime was temporary unavailable.
    """

    INVALID_JOB_PARAMS = 'invalid_job_params'
    SUBMIT_ERROR = 'submit_error'
    # Node reached timeout and timeout service forced it to be done
    NODE_TIMEOUT = 'node_timeout'


class KernelVersion(BaseModel):
    """Linux kernel version model"""
    version: StrictInt = Field(
        description="Major version number e.g. 4 in 'v4.19'"
    )
    patchlevel: StrictInt = Field(
        description="Minor version number or 'patch level' e.g. 19 in 'v4.19'"
    )
    sublevel: Optional[StrictInt] = Field(
        description="Stable version or 'sub-level' e.g. 123 in 'v4.19.123'"
    )
    extra: Optional[str] = Field(
        description="Extra version string e.g. -rc2 in 'v4.19-rc2'"
    )
    name: Optional[str] = Field(
        description="Version name e.g. People's Front for v4.19"
    )

    _STRICT_INT_FIELDS = ['version', 'patchlevel', 'sublevel']

    @classmethod
    def translate_version_fields(cls, params):
        """Translate `StrictInt` field values into `int`"""
        for key, value in params.items():
            if key in cls._STRICT_INT_FIELDS:
                params[key] = int(value)
        return params


class Revision(BaseModel):
    """Linux kernel Git revision model"""
    tree: str = Field(
        description="git tree of the revision"
    )
    url: AnyUrl | FileUrl = Field(
        description="git URL of the revision"
    )
    branch: str = Field(
        description="git branch of the revision"
    )
    commit: str = Field(
        description="git commit SHA of the revision"
    )
    describe: Optional[str] = Field(
        description="git describe of the revision"
    )
    version: Optional[KernelVersion] = Field(
        description="Kernel version"
    )
    patchset: Optional[str] = Field(
        description="Patchset hash"
    )


class DefaultTimeout:
    """Helper to create default values for timeout fields

    The `hours` and `minutes` provided are used to create a `timedelta` object
    available in the `.delta` attribute.  This can then be used to get a
    timeout value used as a default when defining a non-optional field in a
    model with the `.get_timeout()` method.
    """

    def __init__(self, hours=0, minutes=0):
        self._delta = timedelta(hours=hours, minutes=minutes)

    @property
    def delta(self):
        """Get the timedelta set in this object"""
        return self._delta

    def get_timeout(self):
        """Get a timeout timestamp with current time and delta"""
        return datetime.utcnow() + self.delta


class Node(DatabaseModel):
    """KernelCI primitive object to model a node in a hierarchy"""
    class_kind: ClassVar[str] = 'node'
    kind: str = Field(
        default='node',
        description="Type of the object"
    )
    name: str = Field(
        description="Name of the node object"
    )
    path: List[str] = Field(
        description="Full path with node names from the top-level node"
    )
    group: Optional[str] = Field(
        description="Name of a group this node belongs to"
    )
    parent: Optional[PyObjectId] = Field(
        description="Parent commit SHA"
    )
    state: StateValues = Field(
        default=StateValues.RUNNING.value,
        description="State of the node"
    )
    result: Optional[ResultValues] = Field(
        description="Result of node"
    )
    artifacts: Optional[Dict[str, AnyHttpUrl]] = Field(
        description="Artifacts associated with the node (binaries, logs...)"
    )
    data: Optional[Dict[str, Any]] = Field(
        description="Arbitrary data stored in the node"
    )
    debug: Optional[Dict[str, Any]] = Field(
        description="Debug info fields (for development purposes)"
    )
    created: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of node creation"
    )
    updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when node was last updated"
    )
    timeout: datetime = Field(
        default_factory=DefaultTimeout(hours=6).get_timeout,
        description="Node expiry timestamp"
    )
    holdoff: Optional[datetime] = Field(
        description="Node expiry timestamp while in Available state"
    )
    owner: Optional[str] = Field(
        description="Username of node owner"
    )
    user_groups: List[str] = Field(
        default=[],
        description="User groups that are permitted to update node"
    )

    _OBJECT_ID_FIELDS = ['parent']
    _TIMESTAMP_FIELDS = ['created', 'updated', 'timeout', 'holdoff']

    def update(self):
        self.updated = datetime.utcnow()

    @classmethod
    def _translate_operators(cls, params):
        """Translate fields with an operator

        The request query parameters can be provided with operators such `ne`,
        `lt`, `gt`, `lte`, and `gte` with `param__operator=value` format.
        This method will generate translated parameters of the form:

          `parameter, (operator, value)`

        when an operator is found, otherwise:

          `parameter, value`
        """
        for key, value in params.items():
            field = key.split('__')
            if len(field) == 2:
                param, op_name = field
                yield param, (op_name, value)
            else:
                yield key, value

    @classmethod
    def _translate_object_ids(cls, params):
        """Translate ObjectId fields into ObjectId instances

        Generate 2-tuple (key, value) objects for the parameters that need to
        be converted to ObjectId.
        """
        for key, value in params.items():
            if key in cls._OBJECT_ID_FIELDS:
                yield key, ObjectId(value)

    @classmethod
    def _translate_timestamps(cls, params):
        """Translate timestamp fields

        Translate ISOformat timestamp fields as Date objects.  This supports
        translation of fields provided along with operators as well.  It will
        generate the translated parameters of the form:

          `field, (operator, datetime)`

        when an operator is found, otherwise:

          `field, datetime`
        """
        for key, value in params.items():
            if key in cls._TIMESTAMP_FIELDS:
                if isinstance(value, tuple) and len(value) == 2:
                    op_key, op_value = value
                    yield key, (op_key, datetime.fromisoformat(op_value))
                else:
                    yield key, datetime.fromisoformat(value)

    @classmethod
    def translate_fields(cls, params: dict):
        """Translate fields in `params` into objects as applicable

        Translate fields represented by strings in the `params` dictionary into
        objects that match the model.  For example, database IDs are converted
        to ObjectId.  Return a new dictionary with the translated values
        replaced.
        """
        translated = dict(cls._translate_operators(params))
        translated.update(cls._translate_object_ids(translated))
        translated.update(cls._translate_timestamps(translated))
        return translated

    def validate_node_state_transition(self, new_state):
        """Validate Node.state transitions"""
        if new_state == self.state:
            return True, f"Transition to the same state: { new_state }. \
                No validation is required."
        state_transition_map = {
            'running': ['available', 'closing', 'done'],
            'available': ['closing', 'done'],
            'closing': ['done'],
            'done': []
        }
        valid_states = state_transition_map[self.state]
        if new_state not in valid_states:
            return False, f"Transition not allowed with state: {new_state}"
        return True, "Transition validated successfully"


class Hierarchy(BaseModel):
    """Hierarchy of nodes with child nodes"""
    node: Node
    child_nodes: List['Hierarchy']


Hierarchy.update_forward_refs()


class CheckoutData(BaseModel):
    """Model for the data field of a Checkout node"""
    kernel_revision: Optional[Revision] = Field(
        description="Kernel repo revision data"
    )


class Checkout(Node):
    """API model for checkout nodes"""
    class_kind: ClassVar[str] = 'checkout'
    kind: str = Field(
        default='checkout',
        description='Type of the object',
        const=True
    )
    data: CheckoutData = Field(
        description="Checkout details"
    )


class KbuildData(BaseModel):
    """Model for the data field of a Kbuild node"""
    # [TODO] Can be fetched from parent checkout node
    kernel_revision: Optional[Revision] = Field(
        description="Kernel repo revision data"
    )
    arch: Optional[str] = Field(
        description="CPU architecture family"
    )
    defconfig: Optional[str] = Field(
        description="Kernel defconfig identifier"
    )
    compiler: Optional[str] = Field(
        description="Compiler used for the build"
    )
    error_code: Optional[ErrorCodes] = Field(
        description="Details of the failure state"
    )
    fragments: Optional[List[str]] = Field(
        description="List of additional configuration fragments used"
    )
    platform: Optional[str] = Field(
        description="Build platform"
    )
    runtime: Optional[str] = Field(
        description="Runtime that runs the build"
    )
    job_id: Optional[str] = Field(
        description="Runtime job ID"
    )
    job_context: Optional[str] = Field(
        description="Kubernetes cluster name the job submitted to"
    )
    kernel_type: Optional[str] = Field(
        description="Kernel image type (zimage, bzimage...)"
    )


class Kbuild(Node):
    """API model for kbuild (kernel builds) nodes"""
    class_kind: ClassVar[str] = 'kbuild'
    kind: str = Field(
        default='kbuild',
        description='Type of the object',
        const=True
    )
    data: KbuildData = Field(
        description="Kbuild details"
    )


class TestData(BaseModel):
    """Model for the data field of a Test node"""
    error_code: Optional[ErrorCodes] = Field(
        description="Details of the failure state"
    )
    # [TODO] Specify the source code file/function too?
    test_source: Optional[AnyUrl] = Field(
        description="Repository containing the test source code"
    )
    test_revision: Optional[Revision] = Field(
        description="Test repo revision data"
    )
    platform: Optional[str] = Field(
        description="Test platform"
    )
    runtime: Optional[str] = Field(
        description="Runtime that runs the test"
    )
    job_id: Optional[str] = Field(
        description="Runtime job ID"
    )
    job_context: Optional[str] = Field(
        description="Kubernetes cluster name the job submitted to"
    )

    # Fields inherited from the parent kbuild or test case node

    kernel_revision: Optional[Revision] = Field(
        description="Kernel repo revision data"
    )
    arch: Optional[str] = Field(
        description="CPU architecture family"
    )
    defconfig: Optional[str] = Field(
        description="Kernel defconfig identifier"
    )
    compiler: Optional[str] = Field(
        description="Compiler used for the build"
    )
    kernel_type: Optional[str] = Field(
        description="Kernel image type (zimage, bzimage...)"
    )


class Test(Node):
    """API model for test nodes"""
    class_kind: ClassVar[str] = 'test'
    kind: str = Field(
        default='test',
        description='Type of the object',
        const=True
    )
    data: TestData = Field(
        description="Test details"
    )

    def is_test_suite(self):
        """Returns True if the node represents a test suite, false
        otherwise (test case)
        """
        return self.name == self.group


class RegressionData(BaseModel):
    """Model for the data field of a Regression node"""
    fail_node: Optional[PyObjectId] = Field(
        description="Node where the regression was introduced"
    )
    pass_node: Optional[PyObjectId] = Field(
        description="Previous passing Node"
    )
    failed_kernel_revision: Optional[Revision] = Field(
        description="Kernel repo revision data of the failed test run"
    )
    arch: Optional[str] = Field(
        description="CPU architecture family"
    )
    defconfig: Optional[str] = Field(
        description="Kernel defconfig identifier"
    )
    compiler: Optional[str] = Field(
        description="Compiler used for the build"
    )
    platform: Optional[str] = Field(
        description="Test platform"
    )


class Regression(Node):
    """API model for regression tracking"""
    class_kind: ClassVar[str] = 'regression'
    kind: str = Field(
        default='regression',
        description='Type of the object',
        const=True
    )
    data: RegressionData = Field(
        description="Regression details"
    )

    _OBJECT_ID_FIELDS = Node._OBJECT_ID_FIELDS + [
        'data.fail_node',
        'data.pass_node',
    ]
    _TIMESTAMP_FIELDS = Node._TIMESTAMP_FIELDS + [
        'data.fail_node.created',
        'data.fail_node.updated',
        'data.fail_node.timeout',
        'data.fail_node.holdoff',
        'data.pass_node.created',
        'data.pass_node.updated',
        'data.pass_node.timeout',
        'data.pass_node.holdoff',
    ]

    @classmethod
    def create_regression(cls, fail_node, pass_node, as_dict=False):
        """Builds and returns a Regression object from two source nodes:
        a failing and a passing node. These two nodes are assumed to be
        from two different runs of the same test/build with the same
        configuration. pass_node is the last instance of the test/build
        that passed and fail_node is the first one that failed.

        The returned Regression will be an in-memory python object not
        backed up in the DB, which can then be handled and used in a
        node submit request.

        If 'as_dict' is True, the Regression is returned as a dict
        rather than as a Regression object.

        May raise a RuntimeError if any of the sanity checks fail.
        """
        # Sanity checks:
        # - fail_node and pass_node must refer to two
        #   different runs of the same test/build,
        # - fail node must have run after pass_node
        # - pass and fail nodes must have correct results (pass and
        #   fail, respectively)
        error_msg = ("Error creating regression for nodes "
                     f"{pass_node.id} (last passed) and "
                     f"{fail_node.id} (first failed). ")
        cmp_fields = ['name',
                      'group',
                      'path',
                      'data.kernel_revision',
                      'data.arch',
                      'data.defconfig',
                      'data.compiler',
                      'data.platform',]
        for field in cmp_fields:
            getter = attrgetter(field)
            if getter(fail_node) != getter(pass_node):
                raise RuntimeError(error_msg +
                                   f"{field} is different in the fail node "
                                   f"({getter(fail_node)} than in the pass "
                                   f"node ({getter(pass_node)})")
        if pass_node.created > fail_node.created:
            raise RuntimeError(error_msg + "The fail node was created before "
                               "the pass node")
        if pass_node.result != 'pass':
            raise RuntimeError(error_msg + "The pass node has a wrong result: "
                               f"{pass_node.result}")
        if fail_node.result != 'fail':
            raise RuntimeError(error_msg + "The fail node has a wrong result: "
                               f"{fail_node.result}")
        # End of sanity checks
        data_field = {
            'arch': fail_node.data.arch,
            'defconfig': fail_node.data.defconfig,
            'compiler': fail_node.data.compiler,
            'platform': fail_node.data.platform,
            'failed_kernel_revision': fail_node.data.kernel_revision,
            'fail_node': fail_node.id,
            'pass_node': pass_node.id,
        }
        regression_obj = cls(name=fail_node.name,
                             path=fail_node.path,
                             group=fail_node.group,
                             data=data_field,
                             state=StateValues.DONE.value)
        if as_dict:
            regression_json = regression_obj.json(exclude_none=True)
            return json.loads(regression_json)
        return regression_obj


class PublishEvent(BaseModel):
    """API model for the data of a <publish> event"""
    data: Any = Field(
        description="Event payload"
    )
    type: Optional[str] = Field(
        description="Type of the <publish> event"
    )
    source: Optional[str] = Field(
        description="Source of the <publish> event"
    )
    attributes: Optional[Dict] = Field(
        description="Extra Cloudevents Extension Context Attributes"
    )


def parse_node_obj(node: Node | dict):
    """Parses a generic Node object using the appropriate Node submodel
    depending on its 'kind'.

    If the node is passed as a Node object, it returns the appropriate
    submodel object.
    If it's passed as a dict, it's converted to the appropriate Node
    submodel object.
    If it's passed as a concrete Node submodel object, it's returned as
    is.
    """
    if isinstance(node, dict):
        node = Node.parse_obj(node)
    for submodel in Node.__subclasses__():
        if node.kind == submodel.class_kind:
            return submodel.parse_obj(node)
    raise ValueError(f"Unsupported node kind: {node.kind}")
