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

from .conftest import APIHelperTestData


def test_api_init(get_api_config):
    """Test that all the API configurations can be initialised (offline)"""
    for api_name, api_config in get_api_config.items():
        print(f"API config name: {api_name}")
        api = kernelci.api.get_api(api_config)
        assert isinstance(api, kernelci.api.API)
        helper = kernelci.api.helper.APIHelper(api)
        assert isinstance(helper, kernelci.api.helper.APIHelper)


def test_subscribe_without_filter(get_api_config, mock_api_subscribe):
    """Test method used to subscribe the `node` channel without any filters"""
    for _, api_config in get_api_config.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        sub_id = helper.subscribe_filters()
        assert isinstance(sub_id, int)


def test_subscribe_with_filter(get_api_config, mock_api_subscribe):
    """Test method used to subscribe the `test` channel with filter"""
    for _, api_config in get_api_config.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        sub_id = helper.subscribe_filters(
            filters={"name": "checkout"},
            channel="test"
        )
        assert isinstance(sub_id, int)


def test_unsubscribe(get_api_config, mock_api_unsubscribe):
    "Test method used to unsubscribe"
    for _, api_config in get_api_config.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        helper.unsubscribe_filters(sub_id=1)


def test_get_node_from_event(get_api_config, mock_api_get_node_from_id):
    "Test method to get node from CloudEvent data"
    for _, api_config in get_api_config.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        node = helper.get_node_from_event(
            APIHelperTestData().get_test_cloud_event()
        )
        assert node.keys() == {
            'id',
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


def test_submit_regression(get_api_config, mock_api_post_regression):
    """Test method to submit regression object to API"""
    for _, api_config in get_api_config.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        resp = helper.submit_regression(
            regression=APIHelperTestData().regression_node
        )
        assert resp.status_code == 200
        assert resp.json().keys() == {
            'id',
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


def test_pubsub_event_filter_positive(get_api_config, mock_api_subscribe):
    """Test PubSub event filter
    This is a positive test where pubsub event matches provided
    subscription filter. Hence, `helper.pubsub_event_filter` is
    expected to return `True`."""
    for _, api_config in get_api_config.items():
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


def test_pubsub_event_filter_negative(get_api_config, mock_api_subscribe):
    """Test PubSub event filter
    This is a negative test where pubsub event does not matche provided
    subscription filter. Hence, `helper.pubsub_event_filter` is
    expected to return `False`."""
    for _, api_config in get_api_config.items():
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


def test_submit_results(get_api_config, mock_api_put_nodes,
                        mock_api_get_node_from_id):
    """Test method to submit a hierarchy of results"""
    for _, api_config in get_api_config.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        results = {
            "node": APIHelperTestData().kunit_node,
            "child_nodes": [
                {
                    "node": APIHelperTestData().kunit_child_node,
                    "child_nodes": []
                }
            ]
        }
        resp = helper.submit_results(
                results=results,
                root=APIHelperTestData().kunit_node,
            )
        assert len(resp) == 2
        assert resp[1].keys() == {
            'id',
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


def test_receive_event_node(get_api_config, mock_receive_event,
                            mock_api_get_node_from_id, mock_api_subscribe):
    """Test method to receive node from event"""
    for _, api_config in get_api_config.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        sub_id = helper.subscribe_filters(
            filters={
                "op": "created"
            },
        )
        resp = helper.receive_event_node(sub_id=sub_id)
        assert resp.keys() == {
            'id',
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


def test_prepare_results(get_api_config, mock_api_get_node_from_id):
    """Test method to prepare hierarchy of test results"""
    for _, api_config in get_api_config.items():
        api = kernelci.api.get_api(api_config)
        helper = kernelci.api.helper.APIHelper(api)
        root = APIHelperTestData().kunit_node
        child_node = APIHelperTestData().kunit_child_node
        results = {
            "node": root,
            "child_nodes": [
                {
                    "node": child_node,
                    "child_nodes": []
                }
            ]
        }
        base = {
            'revision': root['revision'],
            'group': root['name'],
            'state': 'done',
        }
        parent = api.node.get(root['parent'])
        resp = helper._prepare_results(  # pylint: disable=protected-access
            results, parent, base
        )
        assert resp["node"] == root
        assert set(resp["child_nodes"][0]["node"]) == {
            'artifacts',
            'group',
            'name',
            'parent',
            'path',
            'result',
            'revision',
            'state',
        }
