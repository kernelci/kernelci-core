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


_IMAGE_NOT_OVERRIDDEN = object()


class Job(YAMLConfigObject):
    """Pipeline job definition backed by a validated ``JobConfig``."""

    yaml_tag = "!Job"

    def __init__(self, name, config=None, **legacy_values):
        """Create a named job from validated configuration.

        ``legacy_values`` keeps the previous ``Job(name, template=..., ...)``
        construction API working while ensuring the schema remains the single
        source of truth for accepted fields.
        """
        if isinstance(config, JobConfig):
            if legacy_values:
                fields = ", ".join(sorted(legacy_values))
                raise TypeError(
                    f"Unexpected fields with validated JobConfig: {fields}"
                )
        else:
            if config is not None:
                legacy_values["template"] = config
            config = JobConfig.model_validate(legacy_values)

        self._name = name
        self._config = config
        self._image_override = _IMAGE_NOT_OVERRIDDEN
        formatted_params = (
            self.format_params(
                copy.deepcopy(self._config.params), self._config.params
            )
            if self._config.params
            else {}
        )
        self._config = self._config.model_copy(
            update={"params": formatted_params}
        )

    def __getattr__(self, name):
        """Delegate configuration fields to the validated schema."""
        if name.startswith("_"):
            raise AttributeError(name)
        config = self.__dict__.get("_config")
        if config is None:
            raise AttributeError(name)
        return getattr(config, name)

    @property
    def name(self):
        """Job name"""
        return self._name

    @property
    def image(self):
        """Runtime image, including an optional runtime override."""
        if self._image_override is _IMAGE_NOT_OVERRIDDEN:
            return self._config.image
        return self._image_override

    @image.setter
    def image(self, value):
        """Override the runtime environment image name."""
        self._image_override = value

    @property
    def params(self):
        """Return isolated parameters passed to the template."""
        return copy.deepcopy(self._config.params)

    def _get_format_map(self):
        """Derive formatting fields directly from the authoritative schema."""
        return self._config.model_dump(exclude={"params", "rules"})

    @classmethod
    def to_yaml(cls, dumper, data):
        """Serialize all schema fields without a separate attribute list."""
        values = data._config.model_dump()
        values["image"] = data.image
        return dumper.represent_mapping("tag:yaml.org,2002:map", values)


def from_yaml(data, _):
    """Create the pipeline job definitions using data loaded from YAML"""
    validated = JobsConfig.model_validate({"jobs": data.get("jobs", {})})
    jobs = {
        name: Job(name=name, config=config)
        for name, config in validated.jobs.items()
    }

    return {
        "jobs": jobs,
    }
