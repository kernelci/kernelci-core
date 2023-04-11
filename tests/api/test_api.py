# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

# Silence pylint error of `unused argument` for all the pytest fixtures
# pylint: disable=unused-argument

"""Unit tests for KernelCI API bindings"""

import kernelci.api
import kernelci.api.helper
import kernelci.config

from .conftest import (
    get_test_cloud_event,
    test_regression_node,
    test_kunit_node,
    test_kunit_child_node,
)


def test_api_init():
    """Test that all the API configurations can be initialised (offline)"""
    config = kernelci.config.load('tests/configs/api-configs.yaml')
    api_configs = config['api_configs']
    for api_name, api_config in api_configs.items():
        print(f"API config name: {api_name}")
        api = kernelci.api.get_api(api_config)
        assert isinstance(api, kernelci.api.API)
        helper = kernelci.api.helper.APIHelper(api)
        assert isinstance(helper, kernelci.api.helper.APIHelper)


def test_subscribe_without_filter(mock_api_subscribe):
    """Test method used to subscribe the `node` channel without any filters"""
    config = kernelci.config.load('tests/configs/api-configs.yaml')
    api_configs = config['api_configs']
    for _, api_config in api_configs.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        sub_id = helper.subscribe_filters()
        assert isinstance(sub_id, int)


def test_subscribe_with_filter(mock_api_subscribe):
    """Test method used to subscribe the `test` channel with filter"""
    config = kernelci.config.load('tests/configs/api-configs.yaml')
    api_configs = config['api_configs']
    for _, api_config in api_configs.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        sub_id = helper.subscribe_filters(
            filters={"name": "checkout"},
            channel="test"
        )
        assert isinstance(sub_id, int)


def test_unsubscribe(mock_api_unsubscribe):
    "Test method used to unsubscribe"
    config = kernelci.config.load('tests/configs/api-configs.yaml')
    api_configs = config['api_configs']
    for _, api_config in api_configs.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        helper.unsubscribe_filters(sub_id=1)


def test_get_node_from_event(mock_api_get_node_from_id):
    "Test method to get node from CloudEvent data"
    config = kernelci.config.load('tests/configs/api-configs.yaml')
    api_configs = config['api_configs']
    for _, api_config in api_configs.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        node = helper.get_node_from_event(event=get_test_cloud_event())
        assert node.keys() == {
            '_id',
            'artifacts',
            'created',
            'group',
            'holdoff',
            'kind',
            'name',
            'path',
            'parent',
            'result',
            'revision',
            'state',
            'timeout',
            'updated',
        }


def test_submit_regression(mock_api_post_regression):
    """Test method to submit regression object to API"""
    config = kernelci.config.load('tests/configs/api-configs.yaml')
    api_configs = config['api_configs']
    for _, api_config in api_configs.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        resp = helper.submit_regression(regression=test_regression_node)
        assert resp.status_code == 200
        assert resp.json().keys() == {
            '_id',
            'artifacts',
            'created',
            'group',
            'holdoff',
            'kind',
            'name',
            'path',
            'parent',
            'result',
            'revision',
            'regression_data',
            'state',
            'timeout',
            'updated',
        }


def test_pubsub_event_filter_positive(mock_api_subscribe):
    """Test PubSub event filter
    This is a positive test where pubsub event matches provided
    subscription filter. Hence, `helper.pubsub_event_filter` is
    expected to return `True`."""
    config = kernelci.config.load('tests/configs/api-configs.yaml')
    api_configs = config['api_configs']
    for _, api_config in api_configs.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        sub_id = helper.subscribe_filters(
            filters={
                "op": "created"
            },
        )

        event_data = {
            "op": "created",
            "id": "6332d8f51a45d41c279e7a01",
        }
        ret = helper.pubsub_event_filter(
            sub_id=sub_id,
            event=event_data
        )
        assert ret is True


def test_pubsub_event_filter_negative(mock_api_subscribe):
    """Test PubSub event filter
    This is a negative test where pubsub event does not matche provided
    subscription filter. Hence, `helper.pubsub_event_filter` is
    expected to return `False`."""
    config = kernelci.config.load('tests/configs/api-configs.yaml')
    api_configs = config['api_configs']
    for _, api_config in api_configs.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        sub_id = helper.subscribe_filters(
            filters={
                "op": "created"
            },
        )

        event_data = {
            "op": "updated",
            "id": "6332d8f51a45d41c279e7a01",
        }
        ret = helper.pubsub_event_filter(
            sub_id=sub_id,
            event=event_data
        )
        assert ret is False


def test_submit_results(mock_api_put_nodes, mock_api_get_node_from_id):
    """Test method to submit a hierarchy of results"""
    config = kernelci.config.load('tests/configs/api-configs.yaml')
    api_configs = config['api_configs']
    for _, api_config in api_configs.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        results = {
            "node": test_kunit_node,
            "child_nodes": [
                {
                    "node": test_kunit_child_node,
                    "child_nodes": []
                }
            ]
        }
        resp = helper.submit_results(
                results=results,
                root=test_kunit_node,
            )
        assert len(resp) == 2
        assert resp[1].keys() == {
            '_id',
            'artifacts',
            'created',
            'group',
            'holdoff',
            'kind',
            'name',
            'path',
            'parent',
            'result',
            'revision',
            'state',
            'timeout',
            'updated',
        }
