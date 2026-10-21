# SPDX-License-Identifier: LGPL-2.1-or-later
"""Reject successful kselftest callbacks that lost their test cases."""

import pytest
import yaml

from kernelci.api.models import ErrorCodes
from kernelci.api.models import TestData as CallbackData
from kernelci.runtime.lava import Callback as LavaCallback
from kernelci.runtime.pull_labs import Callback as PullCallback


def lava_callback(cases=None, setup=True):
    """Model a completed job, including a stage with no captured test signals."""
    stages = [
        {"name": "job", "result": "pass", "metadata": {}},
        {"name": "1_kselftest-coredump", "result": "pass", "metadata": {}},
    ]
    if setup:
        stages.append(
            {"name": "login-action", "result": "pass", "metadata": {}}
        )
    results = {"lava": yaml.safe_dump(stages)}
    if cases is not None:
        results["1_kselftest-coredump"] = yaml.safe_dump(
            [
                {"name": name, "result": result, "metadata": {}}
                for name, result in cases.items()
            ]
        )
    return LavaCallback({"status": LavaCallback.COMPLETE, "results": results})


def job_node(name="kselftest-coredump"):
    """Provide the initial job state supplied by the callback service."""
    return {"id": "test-job", "name": name, "result": "pass", "data": {}}


@pytest.mark.parametrize("setup", [False, True])
@pytest.mark.parametrize("cases", [None, {}])
def test_lava_missing_cases_are_incomplete(setup, cases):
    """Neither stage completion nor a successful login proves tests ran."""
    callback = lava_callback(cases, setup)
    hierarchy = callback.get_hierarchy(callback.get_results(), job_node())

    assert hierarchy["node"]["result"] == "incomplete"
    data = CallbackData.model_validate(hierarchy["node"]["data"])
    assert data.error_code == ErrorCodes.TEST
    assert data.error_msg == "No kselftest cases were reported"


@pytest.mark.parametrize("result", ["pass", "fail"])
def test_lava_reported_cases_determine_result(result):
    """A passing stage must still defer to captured test failures."""
    callback = lava_callback({"coredump_case": result})
    hierarchy = callback.get_hierarchy(callback.get_results(), job_node())

    assert hierarchy["node"]["result"] == result
    assert "error_code" not in hierarchy["node"]["data"]


def test_lava_setup_only_baseline_still_passes():
    """Boot jobs may legitimately report only setup results."""
    callback = lava_callback()
    hierarchy = callback.get_hierarchy(
        callback.get_results(), job_node("baseline-arm64")
    )

    assert hierarchy["node"]["result"] == "pass"


def test_pull_summary_without_cases_is_incomplete():
    """Do not accept a nonzero summary count when its cases are missing."""
    callback = PullCallback({"summary": {"total": 1, "failed": 0}, "tests": {}})
    node = job_node("kselftest-breakpoints-pull-labs")
    node["result"] = callback.get_job_status()
    hierarchy = callback.get_hierarchy(callback.get_results(), node)

    assert hierarchy["node"]["result"] == "incomplete"
    data = CallbackData.model_validate(hierarchy["node"]["data"])
    assert data.error_code == ErrorCodes.TEST


@pytest.mark.parametrize("result", ["pass", "fail", "skip"])
def test_pull_reported_cases_determine_result(result):
    """Individual results remain authoritative even with a passing summary."""
    callback = PullCallback(
        {
            "summary": {"total": 1, "failed": 0},
            "tests": {"breakpoints_case": {"status": result}},
        }
    )
    node = job_node("kselftest-breakpoints-pull-labs")
    node["result"] = callback.get_job_status()
    hierarchy = callback.get_hierarchy(callback.get_results(), node)

    assert hierarchy["node"]["result"] == result
