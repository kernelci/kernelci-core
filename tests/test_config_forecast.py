# SPDX-License-Identifier: LGPL-2.1-or-later

import sys
import types

if "cloudevents.http" not in sys.modules:
    cloudevents = types.ModuleType("cloudevents")
    cloudevents_http = types.ModuleType("cloudevents.http")
    cloudevents_http.CloudEvent = object
    sys.modules["cloudevents"] = cloudevents
    sys.modules["cloudevents.http"] = cloudevents_http


def _forecast_module():
    from kernelci.cli import config

    return config


def _forecast_data():
    return {
        "build_configs": {
            "mainline": {
                "tree": "mainline",
                "branch": "master",
                "architectures": ["arm64"],
            }
        },
        "jobs": {
            "kbuild-gcc-14-arm64": {
                "kind": "kbuild",
                "params": {
                    "arch": "arm64",
                    "compiler": "gcc-14",
                    "defconfig": "defconfig",
                    "fragments": ["kselftest"],
                },
            },
            "ltp-syscalls": {
                "kind": "job",
                "rules": {
                    "fragments": ["!kselftest"],
                },
            },
        },
        "platforms": {
            "bcm2711-rpi-4-b": {},
        },
        "scheduler": [
            {
                "job": "kbuild-gcc-14-arm64",
                "event": {
                    "channel": "node",
                    "kind": "checkout",
                    "state": "available",
                },
                "runtime": {
                    "name": "k8s-all",
                },
            },
            {
                "job": "ltp-syscalls",
                "event": {
                    "channel": "node",
                    "kind": "kbuild",
                    "name": "kbuild-gcc-14-arm64",
                    "state": "available",
                },
                "runtime": {
                    "name": "lava-collabora",
                },
                "platforms": ["bcm2711-rpi-4-b"],
            },
        ],
    }


def test_forecast_tests_uses_kbuild_params_for_rule_evaluation():
    checkout = {
        "tree": "mainline",
        "branch": "master",
        "architectures": ["arm64"],
    }

    tests = _forecast_module().forecast_tests(
        _forecast_data(),
        "kbuild-gcc-14-arm64",
        checkout,
    )

    assert tests == []


def test_explain_forecast_job_reports_blocked_rule():
    lines = _forecast_module().explain_forecast_job(
        _forecast_data(),
        "ltp-syscalls",
        "mainline",
        "master",
        platform="bcm2711-rpi-4-b",
    )

    assert "Result: not scheduled" in lines
    assert any(
        "job ltp-syscalls: rules[fragments] rejects ['kselftest']" in line
        for line in lines
    )
