# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""KernelCI API helpers"""

from typing import Dict

from . import API


class APIHelper:
    """API helper base class

    This provides some common middleware between the API class and
    applications.
    """

    def __init__(self, api: API):
        self._api = api
        self._filters: Dict[str, Dict[str, str]] = {}

    @property
    def api(self):
        """API object"""
        return self._api

    def subscribe_filters(self, filters=None, channel='node'):
        """Subscribe to a channel with some added filters"""
        sub_id = self.api.subscribe(channel)
        self._filters[sub_id] = filters
        return sub_id

    def unsubscribe_filters(self, sub_id):
        """Unsubscribe from a channel with previously registered filters"""
        if sub_id in self._filters:
            self._filters.pop(sub_id)
        self.api.unsubscribe(sub_id)

    def get_node_from_event(self, event):
        """Listen for an event and get the matching node object from it"""
        return self.api.get_node(event.data['id'])

    def pubsub_event_filter(self, sub_id, event):
        """Filter Pub/Sub events

        Filter received Pub/Sub event using provided filter dictionary.
        Return True if client has not provided any filter dictionary.
        If filters are provided, return True if the event data matches with
        the filter parameters, otherwise False.
        """
        filters = self._filters.get(sub_id)
        if not filters:
            return True
        for key, value in filters.items():
            if key not in event.keys():
                continue
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in event.get(key):
                        continue
                    if isinstance(sub_value, tuple):
                        if not any(sub_sub_value == event.get(key).get(sub_key)
                                   for sub_sub_value in sub_value):
                            return False
                    elif sub_value != event.get(key).get(sub_key):
                        return False
            elif isinstance(value, tuple):
                if not any(sub_value == event[key] for sub_value in value):
                    return False
            elif value != event[key]:
                return False

        return True

    def receive_event_node(self, sub_id):
        """
        Listen to all the events on 'node' channel and apply filter on it.
        Return node if event matches with the filter.
        """
        while True:
            event = self.api.receive_event(sub_id)
            node = self.get_node_from_event(event)
            if all(self.pubsub_event_filter(sub_id, obj)
                   for obj in [node, event.data]):
                return node

    def submit_regression(self, regression):
        """Post a regression object

        It is still unclear whether regressions should have their own separate
        endpoint or just be added to the nodes collection with a different
        'kind' field.  For now, treat this as a middleware feature on top of
        the established API endpoints.
        """
        # pylint: disable=protected-access
        return self.api._post('regression', regression)
