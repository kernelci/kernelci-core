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
