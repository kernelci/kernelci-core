# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2018-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

# mypy: ignore-errors

"""Common classes for all YAML pipeline config types"""

import copy
import re

import yaml


class YAMLConfigObject(yaml.YAMLObject):
    """Base class with helper methods to handle configuration YAML data

    This class contains methods to help constructing configuration objects from
    YAML data.  Then each subclass should implement its standard `to_yaml()`
    method to be able to dump the whole configuration hierarchy back to YAML.
    """

    @classmethod
    def load_from_yaml(cls, config, **kwargs):
        """Load the YAML configuration

        Load the YAML configuration passed as a *config* data structure with a
        given *name*.  This method should return an instance of a
        YAMLConfigObject subclass.
        """
        yaml_attributes = cls._get_yaml_attributes()
        kwargs.update(cls._kw_from_yaml(config, yaml_attributes))
        return cls(**kwargs)

    @classmethod
    def _kw_from_yaml(cls, data, attributes):
        """Create some keyword arguments based on a YAML dictionary

        Return a dictionary suitable to be used as Python keyword arguments in
        an object constructor using values from some YAML *data*.  The
        *attributes* are a list of keys to look up from the *data* and convert
        to a dictionary.  Keys that are not in the YAML data are simply omitted
        from the returned keywords, relying on default values in object
        constructors.

        """
        return {
            k: v for k, v in ((k, data.get(k))for k in attributes)
            if v is not None
        } if data else {}

    @classmethod
    def _get_yaml_attributes(cls):
        """Get a set of YAML attribute names

        Get a set object with all the YAML configuration attribute names for
        the configuration class.  This can be used to make keyword arguments
        when creating a configuration object as well as when serialising it
        back to YAML.
        """
        return set()

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_mapping(
            'tag:yaml.org,2002:map', {
                key: getattr(data, key)
                for key in cls._get_yaml_attributes()
            }
        )


class _YAMLObject:
    """Base class with helper methods to initialise objects from YAML data."""

    @classmethod
    def from_yaml(cls, config, **kwargs):
        """Load the YAML configuration

        Load the YAML configuration passed as a *config* data structure with a
        given *name*.  This method should return an instance of a _YAMLObject
        subclass.
        """
        yaml_attributes = cls._get_yaml_attributes()
        kwargs.update(cls._kw_from_yaml(config, yaml_attributes))
        return cls(**kwargs)

    @classmethod
    def _kw_from_yaml(cls, data, attributes):
        """Create some keyword arguments based on a YAML dictionary

        Return a dictionary suitable to be used as Python keyword arguments in
        an object constructor using values from some YAML *data*.  The
        *attributes* are a list of keys to look up from the *data* and convert
        to a dictionary.  Keys that are not in the YAML data are simply omitted
        from the returned keywords, relying on default values in object
        constructors.

        """
        return {
            k: v for k, v in ((k, data.get(k))for k in attributes)
            if v is not None
        } if data else {}

    @classmethod
    def _get_yaml_attributes(cls):
        """Get a set of YAML attribute names

        Get a set object with all the YAML configuration attribute names for
        the configuration class.  This can be used to make keyword arguments
        when creating a configuration object as well as when serialising it
        back to YAML.
        """
        return set()

    def to_dict(self):
        """Create a dictionary with the configuration data

        Create a Python dictionary object with key-values representing the
        configuration data originally imported from YAML.  This may not include
        non-serialisable objects such as Filters.
        """
        return {
            attr: value for attr, value in (
                (attr, getattr(self, attr))
                for attr in self._get_yaml_attributes()
            ) if value is not None
        }

    def to_yaml(self):
        """Recreate a YAML representation of the configuration data

        Recreate a YAML text representation of the key-values made available
        via the .to_dict() method.  This can be used to serialise a
        configuration object and load it again without access to the full
        original YAML files.
        """
        return yaml.dump(self.to_dict())


class Filter(YAMLConfigObject):
    """Base class to implement arbitrary configuration filters."""

    def __init__(self, items):
        """The *items* can be any data used to filter configurations."""
        self._items = items

    @property
    def items(self):
        """Filter items"""
        return self._items

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_mapping(
            'tag:yaml.org,2002:map', dict(data.items.items())
        )

    def match(self, **kw):
        """Return True if the given *kw* keywords match the filter."""
        raise NotImplementedError("Filter.match() is not implemented")

    def combine(self, items):  # pylint: disable=unused-argument
        """Try to avoid making a new filter if we can make a combined
        filter matching both our existing data and the new items.

        The *items* can be any data used to filter configurations.
        Return True if we can combine, False otherwise.
        """
        return False


def _merge_filter_lists(old, update):
    """Merge the items for a Blocklist or Passlist.

    *old*    is the items from the existing filter list that we
             have already created.

    *update* are the items of a new filter list, of the same type as
             *old*, loaded from another configuration source. We are
             going represent this second filter list declaration by
             updating *old*, rather than by having a new object to
             represent it.
    """
    for key, value in update.items():
        old.setdefault(key, []).extend(value)


class Blocklist(Filter):
    """Blocklist filter to discard certain configurations.

    Blocklist *items* are a dictionary associating keys with lists of values.
    Any configuration with a key-value pair present in these lists will be
    rejected.
    """

    yaml_tag = '!BlockList'
    name = 'blocklist'

    def match(self, **kwargs):
        for key, value in kwargs.items():
            blocklist = self._items.get(key)
            if not blocklist:
                continue
            if any(item in value for item in blocklist):
                return False

        return True

    def combine(self, items):
        _merge_filter_lists(self._items, items)
        return True


class Passlist(Filter):
    """Passlist filter to only accept certain configurations.

    Passlist *items* are a dictionary associating keys with lists of values.
    For a configuration to be accepted, there must be a value found in each of
    these lists.
    """

    yaml_tag = '!PassList'
    name = 'passlist'

    def match(self, **kwargs):
        for key, passlist in self._items.items():
            value = kwargs.get(key)
            if not value:
                return False
            if not any(item in value for item in passlist):
                return False

        return True

    def combine(self, items):
        _merge_filter_lists(self._items, items)
        return True


class Regex(Filter):
    """Regex filter to only accept certain configurations.

    Regex *items* are a dictionary associating keys with regular expressions.
    The should be one regular expression for each key, not a list of them.  For
    a configuration to be accepted, its value must match the regular expression
    for each key specified in the filter items.
    """

    yaml_tag = '!Regex'
    name = 'regex'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._re_items = {k: re.compile(v) for k, v in self._items.items()}

    def match(self, **kwargs):
        for key, regex in self._re_items.items():
            value = kwargs.get(key)
            return value and regex.match(value)


class Combination(Filter):
    """Combination filter to only accept some combined configurations.

    Combination *items* are a dictionary with 'keys' and 'values'.  The 'keys'
    are a list of keywords to look for, and 'values' are a list of combined
    values for the given keys.  The length of each 'values' item must therefore
    match the length of the 'keys' list, and the order of the values must match
    the order of the keys.
    """

    yaml_tag = '!Combination'
    name = 'combination'

    def __init__(self, items):
        super().__init__(items)
        self._keys = tuple(items['keys'])
        self._values = list(tuple(values) for values in items['values'])

    def match(self, **kwargs):
        filter_values = tuple(kwargs.get(k) for k in self._keys)
        return filter_values in self._values

    def combine(self, items):
        keys = tuple(items['keys'])
        if keys != self._keys:
            return False

        self._values.extend([tuple(values) for values in items['values']])
        return True


class FilterFactory:
    """Factory to create filters from YAML data."""

    _classes = {
        cls.name: cls for cls in [
            Blocklist,
            Passlist,
            Regex,
            Combination,
        ]
    }

    @classmethod
    def load_from_yaml(cls, filter_params):
        """Iterate through the YAML filters and return Filter objects."""
        filter_list = []
        filters = {}

        for fil in filter_params:
            for filter_type, items in fil.items():
                for subfil in filters.get(filter_type, []):
                    if subfil.combine(items):
                        break
                else:
                    filter_cls = cls._classes[filter_type]
                    # We need to provide the new filter with its own
                    # item arrays, so that we don't accidentally
                    # corrupt the initial dictionary we were
                    # passed. That can cause bleed-through, where our
                    # filter terms start being applied in other places
                    # unexpectedly.
                    filter_instance = filter_cls(copy.deepcopy(items))
                    filters.setdefault(filter_type, []).append(
                        filter_instance)
                    filter_list.append(filter_instance)

        return filter_list

    @classmethod
    def from_data(cls, data, default_filters=None):
        """Look for filters in YAML *data* or return *default_filters*.

        Look for a *filters* element in the YAML *data* dictionary.  If there
        is one, iterate over each item to return a list of Filter objects.
        Otherwise, return *default_filters*.
        """
        params = data.get('filters')
        return cls.load_from_yaml(params) if params else default_filters


def default_filters_from_yaml(data):
    """Load the default YAML filters"""
    return {
        entry_type: FilterFactory.load_from_yaml(filters_data)
        for entry_type, filters_data in data.get('default_filters', {}).items()
    }
