# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2021-2024 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

# Disable below flag as some models are just for storing the data and do not
# need methods
# pylint: disable=too-few-public-methods

# pylint: disable=no-name-in-module

"""Common KernelCI API model definitions"""

from typing import Optional, Any, Dict
from bson import ObjectId
from pydantic import (
    BaseModel,
    Field,
    model_serializer,
    SerializationInfo,
)
from pydantic.dataclasses import dataclass
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    """Wrapper around ObjectId to be able to use it in Pydantic models"""

    @classmethod
    def __get_pydantic_core_schema__(
            cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ]),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ])
        )

    @classmethod
    def validate(cls, value):
        """Validate the value of the ObjectId"""
        if not ObjectId.is_valid(value):
            raise ValueError(f"Invalid ObjectId: {value}")
        return ObjectId(value)


class ModelId(BaseModel):
    """Pydantic model including a .id attribute for the Mongo DB _id

    This Pydantic model class is a thin wrapper around `pydantic.BaseModel`
    with an added `.id` attribute which then gets translated to the `_id`
    attribute in Mongo DB documents using the `PyObjectId` class.
    """

    id: Optional[PyObjectId] = Field(None, alias='_id')

    model_config = {
        "arbitrary_types_allowed": True,
        "use_enum_values": True,
        "populate_by_name": True,
    }


class DatabaseModel(ModelId):
    """Database model"""
    @dataclass
    class Index():
        """Index class"""
        field: str
        attributes: dict[str, Any]

    def update(self):
        """Method to update model"""

    @classmethod
    def get_indexes(cls):
        """Method to get indexes"""

    @model_serializer
    def serialize_model(self, info: SerializationInfo) -> Dict[str, Any]:
        """Model serializer for the below custom handling:
        - convert ObjectId fields to string
        - handle `exclude` fields in serialized response
        """
        values = self.__dict__.copy()

        # TODO:  # pylint: disable=fixme
        # Remove manual handling of `exclude` fields below once
        # the pydantic issue is fixed:
        # https://github.com/pydantic/pydantic/issues/6575
        if info.exclude:
            for field in info.exclude:
                values.pop(field, None)

        for field_name, value in values.items():
            if isinstance(value, ObjectId):
                if info.mode == 'json':
                    values[field_name] = str(value)
                else:
                    values[field_name] = value
        return values
