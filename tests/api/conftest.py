# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>


"""pytest fixtures for APIHelper unit tests"""

import json
import pytest
from cloudevents.http import CloudEvent
from cloudevents.conversion import to_json
from requests import Response

import kernelci.config


class APIHelperTestData:
    """Sample test data for APIHelper unit tests"""
    def __init__(self):
        self._checkout_node = {
            "id": "6332d8f51a45d41c279e7a01",
            "kind": "node",
            "name": "checkout",
            "path": [
                "checkout"
            ],
            "group": None,
            "revision": {
                "tree": "kernelci",
                "url": "https://github.com/kernelci/linux.git",
                "branch": "staging-mainline",
                "commit": "7f036eb8d7a5ff2f655c5d949343bac6a2928bce",
                "describe": "staging-mainline-20220927.0",
                "version": {
                    "version": 6,
                    "patchlevel": 0,
                    "sublevel": None,
                    "extra": "-rc7-36-g7f036eb8d7a5",
                    "name": None
                }
            },
            "parent": None,
            "state": "done",
            "result": None,
            "artifacts": {
                "tarball": "http://staging.kernelci.org:9080/linux-kernelci\
    -staging-mainline-staging-mainline-20220927.0.tar.gz"
            },
            "created": "2022-09-27T11:05:25.814000",
            "updated": "2022-09-27T11:15:28.566000",
            "timeout": "2022-09-28T11:05:25.814000",
            "holdoff": None
        }
        self._regression_node = {
            "kind": "regression",
            "name": "kver",
            "path": [
                "checkout",
                "kver"
            ],
            "group": "kver",
            "revision": {
                "tree": "kernelci",
                "url": "https://github.com/kernelci/linux.git",
                "branch": "staging-mainline",
                "commit": "cef45fe0b71c5f51ef956a026bd71a64ca7f8300",
                "describe": "staging-mainline-20221101.1",
                "version": {
                    "version": 6,
                    "patchlevel": 1,
                    "sublevel": None,
                    "extra": "-rc3-13-gcef45fe0b71c",
                    "name": None
                }
            },
            "parent": "6361440f8f94e20c6826b0b7",
            "state": "done",
            "result": "pass",
            "artifacts": {
                "tarball": "http://staging.kernelci.org:9080/linux-kernelci\
        -staging-mainline-staging-mainline-20221101.1.tar.gz"
            },
            "created": "2022-11-01T16:07:09.770000",
            "updated": "2022-11-01T16:07:09.770000",
            "timeout": "2022-11-02T16:07:09.770000",
            "holdoff": None,
            "regression_data": [
                {
                    "id": "6361440f8f94e20c6826b0b7",
                    "kind": "node",
                    "name": "kver",
                    "path": [
                        "checkout",
                        "kver"
                    ],
                    "group": "kver",
                    "revision": {
                        "tree": "kernelci",
                        "url": "https://github.com/kernelci/linux.git",
                        "branch": "staging-mainline",
                        "commit": "cef45fe0b71c5f51ef956a026bd71a64ca7f8300",
                        "describe": "staging-mainline-20221101.1",
                        "version": {
                            "version": 6,
                            "patchlevel": 1,
                            "sublevel": None,
                            "extra": "-rc3-13-gcef45fe0b71c",
                            "name": None
                        }
                    },
                    "parent": "636143c38f94e20c6826b0b6",
                    "state": "done",
                    "result": "pass",
                    "artifacts": {
                        "tarball": "http://staging.kernelci.org:9080/linux-\
        kernelci-staging-mainline-staging-mainline-20221101.1.tar.gz"
                    },
                    "created": "2022-11-01T16:06:39.509000",
                    "updated": "2022-11-01T16:07:09.633000",
                    "timeout": "2022-11-02T16:06:39.509000",
                    "holdoff": None
                }
            ]
        }
        self._kunit_node = {
            "id": "6332d92f1a45d41c279e7a06",
            "kind": "node",
            "name": "kunit",
            "path": [
                "checkout",
                "kunit"
            ],
            "group": "kunit",
            "revision": {
                "tree": "kernelci",
                "url": "https://github.com/kernelci/linux.git",
                "branch": "staging-mainline",
                "commit": "7f036eb8d7a5ff2f655c5d949343bac6a2928bce",
                "describe": "staging-mainline-20220927.0",
                "version": {
                    "version": 6,
                    "patchlevel": 0,
                    "sublevel": None,
                    "extra": "-rc7-36-g7f036eb8d7a5",
                    "name": None
                }
            },
            "parent": "6332d8f51a45d41c279e7a01",
            "state": "done",
            "result": None,
            "artifacts": {
                "tarball": "http://staging.kernelci.org:9080/linux-kernelci-\
    staging-mainline-staging-mainline-20220927.0.tar.gz"
            }
        }
        self._kunit_child_node = {
            "name": "time_test_cases",
            "parent": "6332d92f1a45d41c279e7a06",
            "result": "pass",
            "artifacts": {
                "tarball": "http://staging.kernelci.org:9080/linux-kernelci-\
        staging-mainline-staging-mainline-20220927.0.tar.gz"
            }
        }

    @property
    def checkout_node(self):
        """Get the checkout node"""
        return self._checkout_node

    @property
    def regression_node(self):
        """Get the regression node"""
        return self._regression_node

    @property
    def kunit_node(self):
        """Get the kunit node"""
        return self._kunit_node

    @property
    def kunit_child_node(self):
        """Get the kunit sample child node"""
        return self._kunit_child_node

    def get_regression_node_with_id(self):
        """Get regression node with node ID"""
        self._regression_node.update({
            "id": "6361442d8f94e20c6826b0b9"
        })
        return self._regression_node

    def update_kunit_node(self):
        """Update kunit node with timestamp fields"""
        self._kunit_node.update({
            "created": "2022-11-01T16:06:39.509000",
            "updated": "2022-11-01T16:07:09.633000",
            "timeout": "2022-11-02T16:06:39.509000",
            "holdoff": None,
        })
        return self._kunit_node

    def update_kunit_child_node(self):
        """Update kunit child node with timestamp fields and other fields set
        from parent kunit"""
        self._kunit_child_node.update({
            "id": "6332d9741a45d41c279e7a07",
            "created": "2022-11-01T16:06:39.509000",
            "group": self._kunit_node["group"],
            "holdoff": None,
            "kind": self._kunit_node["kind"],
            "path": (
                self._kunit_node["path"] + [self._kunit_child_node["name"]]
            ),
            "revision": self._kunit_node["revision"],
            "state": self._kunit_node["state"],
            "timeout": "2022-11-02T16:06:39.509000",
            "updated": "2022-11-01T16:07:09.633000",
        })
        return self._kunit_child_node

    def get_test_cloud_event(self):
        """Get test CloudEvent instance"""
        attributes = {
            "type": "api.kernelci.org",
            "source": "https://api.kernelci.org/",
        }
        data = {
            "op": "created",
            "id": self.checkout_node["id"],
        }
        return CloudEvent(attributes=attributes, data=data)


@pytest.fixture
def get_api_config():
    """Fixture to get API configurations"""
    config = kernelci.config.load('tests/configs/api-configs.yaml')
    api_configs = config['api']
    return api_configs


@pytest.fixture
def mock_api_subscribe(mocker):
    """Mocks call to LatestAPI class method used to subscribe"""
    mocker.patch(
        'kernelci.api.latest.LatestAPI.subscribe',
        return_value=1
    )


@pytest.fixture
def mock_api_unsubscribe(mocker):
    """Mocks call to LatestAPI class method used to unsubscribe"""
    mocker.patch('kernelci.api.latest.LatestAPI.unsubscribe')


@pytest.fixture
def mock_api_get_node_from_id(mocker):
    """Mocks call to LatestAPI class method used to get node from node ID"""
    mocker.patch(
        'kernelci.api.latest.LatestAPI.Node.get',
        return_value=APIHelperTestData().checkout_node,
    )


@pytest.fixture
def mock_api_post_regression(mocker):
    """Mocks call to LatestAPI class method used to submit regression node"""
    resp = Response()
    resp.status_code = 200
    resp._content = json.dumps(  # pylint: disable=protected-access
        APIHelperTestData().get_regression_node_with_id()).encode('utf-8')

    mocker.patch(
        'kernelci.api.API._post',
        return_value=resp,
    )


@pytest.fixture
def mock_api_put_nodes(mocker):
    """
    Mocks call to LatestAPI class method used to submit hierarchy of node
    results
    """
    resp = Response()
    resp.status_code = 200
    resp_data = [
        APIHelperTestData().update_kunit_node(),
        APIHelperTestData().update_kunit_child_node()
    ]
    resp._content = json.dumps(  # pylint: disable=protected-access
        resp_data).encode('utf-8')
    mocker.patch(
        'kernelci.api.API._put',
        return_value=resp,
    )


@pytest.fixture
def mock_receive_event(mocker):
    """
    Mocks call to LatestAPI class method used to receive CloudEvent
    """
    resp = Response()
    resp.status_code = 200
    event = APIHelperTestData().get_test_cloud_event()
    resp._content = to_json(event)  # pylint: disable=protected-access
    mocker.patch(
        'kernelci.api.latest.LatestAPI.receive_event',
        return_value=event,
    )
