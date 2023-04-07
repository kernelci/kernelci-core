# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>


"""pytest fixtures for APIHelper unit tests"""

import json
import pytest
from cloudevents.http import CloudEvent
from requests import Response


test_checkout_node = {
        "_id": "6332d8f51a45d41c279e7a01",
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

test_regression_node = {
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
            "_id": "6361440f8f94e20c6826b0b7",
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


def get_test_cloud_event():
    """Get test CloudEvent instance"""
    attributes = {
        "type": "api.kernelci.org",
        "source": "https://api.kernelci.org/",
    }
    data = {
        "op": "created",
        "id": "6332d8f51a45d41c279e7a01",
    }
    return CloudEvent(attributes=attributes, data=data)


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
        'kernelci.api.latest.LatestAPI.get_node',
        return_value=test_checkout_node,
    )


@pytest.fixture
def mock_api_post_regression(mocker):
    """Mocks call to LatestAPI class method used to submit regression node"""
    test_regression_node["_id"] = "6361442d8f94e20c6826b0b9"
    resp = Response()
    resp.status_code = 200
    resp._content = json.dumps(  # pylint: disable=protected-access
        test_regression_node).encode('utf-8')

    mocker.patch(
        'kernelci.api.API._post',
        return_value=resp,
    )
