# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>


"""pytest fixtures for APIHelper unit tests"""

import pytest


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
