# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2021-2023 Collabora Limited
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
)
from pydantic.dataclasses import dataclass


class PyObjectId(ObjectId):
    """Wrapper around ObjectId to be able to use it in Pydantic models"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type='string')

    @classmethod
    def validate(cls, value, _info):
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
    def serialize_model(self) -> Dict[str, Any]:
        """Serializer for converting ObjectId to string"""
        values = self.__dict__.copy()
        for field_name, value in values.items():
            if isinstance(value, ObjectId):
                values[field_name] = str(value)
        return values
