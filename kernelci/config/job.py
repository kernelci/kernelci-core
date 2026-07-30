# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI pipeline job configuration"""

import copy
from typing import Annotated, Any, Dict, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .base import YAMLConfigObject

JobPriority = Union[
    Literal["low", "medium", "high"],
    Annotated[int, Field(ge=0, le=100)],
]


class JobConfig(BaseModel):
    """Validated YAML representation of a pipeline job."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    template: str = Field(min_length=1)
    kind: str = "node"
    base_name: Optional[str] = None
    image: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    rules: Any = None
    kcidb_test_suite: Any = None
    priority: Optional[JobPriority] = None


class JobsConfig(BaseModel):
    """Validated top-level pipeline jobs configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    jobs: Dict[str, JobConfig] = Field(default_factory=dict)


class Job(YAMLConfigObject):
    """Pipeline job definition"""

    yaml_tag = "!Job"

    def __init__(
        self,
        name,
        template,
        *,
        kind="node",
        base_name=None,
        image=None,
        params=None,
        rules=None,
        kcidb_test_suite=None,
        priority=None,
    ):
        self._name = name
        self._template = template
        self._kind = kind
        self._base_name = base_name
        self._image = image
        self._kcidb_test_suite = kcidb_test_suite
        self._priority = priority
        self._params = (
            self.format_params(copy.deepcopy(params), params) if params else {}
        )
        self._rules = rules

    @property
    def name(self):
        """Job name"""
        return self._name

    @property
    def template(self):
        """Template file name"""
        return self._template

    @property
    def kind(self):
        """Job node kind"""
        return self._kind

    @property
    def base_name(self):
        """Optional base job name used to group related job variants"""
        return self._base_name

    @property
    def priority(self):
        """Job priority"""
        return self._priority

    @property
    def image(self):
        """Runtime environment image name"""
        return self._image

    @image.setter
    def image(self, value):
        """Set the runtime environment image name"""
        self._image = value

    @property
    def params(self):
        """Arbitrary parameters passed to the template"""
        return copy.deepcopy(self._params)

    @property
    def rules(self):
        """Kernel requirements (tree, branch, version...)"""
        return self._rules

    @property
    def kcidb_test_suite(self):
        """Mapping of KernelCI test to KCIDB test suite"""
        return self._kcidb_test_suite

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update(
            {
                "template",
                "kind",
                "base_name",
                "image",
                "params",
                "rules",
                "kcidb_test_suite",
                "priority",
            }
        )
        return attrs


def from_yaml(data, _):
    """Create the pipeline job definitions using data loaded from YAML"""
    validated = JobsConfig.model_validate({"jobs": data.get("jobs", {})})
    jobs = {
        name: Job(name=name, **config.model_dump())
        for name, config in validated.jobs.items()
    }

    return {
        "jobs": jobs,
    }
