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

from typing import Optional
from bson import ObjectId
from pydantic import (
    BaseModel,
    Field,
)


class PyObjectId(ObjectId):
    """Wrapper around ObjectId to be able to use it in Pydantic models"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type='string')

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

    id: Optional[PyObjectId] = Field(alias='_id')

    class Config:
        """Configuration attributes for ModelId"""
        arbitrary_types_allowed = True
        use_enum_values = True
        json_encoders = {
            ObjectId: str,
        }
        allow_population_by_field_name = True


class DatabaseModel(ModelId):
    """Database model"""
    def update(self):
        """Method to update model"""

    @classmethod
    def create_indexes(cls, collection):
        """Method to create indexes"""
