# SPDX-License-Identifier: LGPL-2.1-or-later

"""Tests for the ``kci docker`` command group."""

from unittest import mock

import click
import docker
import pytest

from kernelci.cli.docker import _do_push


def test_push_retries_registry_error():
    helper = mock.Mock()
    helper.push_image.side_effect = [
        [{"errorDetail": {"message": "unknown blob"}}],
        [{"status": "Pushed"}],
    ]

    with mock.patch("kernelci.cli.docker.time.sleep") as sleep:
        _do_push(helper, "ghcr.io/kernelci/clang-21", "x86", verbose=False)

    assert helper.push_image.call_count == 2
    sleep.assert_called_once_with(5)


def test_push_retries_docker_exception():
    helper = mock.Mock()
    helper.push_image.side_effect = [
        docker.errors.APIError("temporary registry failure"),
        [{"status": "Pushed"}],
    ]

    with mock.patch("kernelci.cli.docker.time.sleep") as sleep:
        _do_push(helper, "ghcr.io/kernelci/clang-21", "x86", verbose=False)

    assert helper.push_image.call_count == 2
    sleep.assert_called_once_with(5)


def test_push_fails_after_three_attempts():
    helper = mock.Mock()
    helper.push_image.return_value = [
        {"errorDetail": {"message": "unknown blob"}}
    ]

    with mock.patch("kernelci.cli.docker.time.sleep") as sleep:
        with pytest.raises(click.ClickException, match="unknown blob"):
            _do_push(
                helper,
                "ghcr.io/kernelci/clang-21",
                "x86",
                verbose=False,
            )

    assert helper.push_image.call_count == 3
    assert sleep.call_args_list == [mock.call(5), mock.call(10)]
