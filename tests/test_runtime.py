# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019 Linaro Limited
# Author: Dan Rue <dan.rue@linaro.org>
#
# Copyright (C) 2019, 2021, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Unit test for KernelCI Runtime implementation"""

# This is normal practice for tests in order to cover parts of the
# implementation.
# pylint: disable=protected-access

import types

import kernelci.config
import kernelci.runtime


class _FakeResponse:
    def __init__(self, payload, status_code=200, text=""):
        """Initialize a fake response with payload and status."""
        self._payload = payload
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        """Raise an error when the response indicates failure."""
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        """Return the preloaded JSON payload."""
        return self._payload


class _FakeSession:
    def __init__(self, get_handler=None, post_handler=None):
        """Initialize a fake session with optional handlers."""
        self._get_handler = get_handler
        self._post_handler = post_handler
        self.calls = []

    def get(self, url, params=None, timeout=30):  # pylint: disable=unused-argument
        """Invoke the GET handler and return a fake response."""
        if not self._get_handler:
            raise AssertionError("GET handler not set")
        self.calls.append((url, params))
        return _FakeResponse(self._get_handler(url, params))

    def post(  # pylint: disable=unused-argument
        self, url, json=None, allow_redirects=False, timeout=30
    ):
        """Invoke the POST handler and return its response."""
        if not self._post_handler:
            raise AssertionError("POST handler not set")
        self.calls.append((url, json))
        return self._post_handler(url, json)


def test_runtimes_init():
    """Test that all the runtimes can be initialised (offline)"""
    config = kernelci.config.load('tests/configs/runtimes.yaml')
    runtimes = config['runtimes']
    for runtime_name, runtime_config in runtimes.items():
        print(f"Runtime name: {runtime_name}")
        kernelci.runtime.get_runtime(runtime_config)


def test_lava_priority_hierarchy():
    """Test LAVA priority: human=highest, tree=high/medium/low"""
    config = kernelci.config.load('tests/configs/lava-runtimes.yaml')
    runtimes = config['runtimes']
    runtime_config = runtimes['lab-min-12-max-40-new-runtime']
    lab = kernelci.runtime.get_runtime(runtime_config)

    job_config_no_priority = type('JobConfig', (), {'priority': None})()

    job_human_high_tree = type('Job', (), {
        'node': {'data': {'tree_priority': 'high'}, 'submitter': 'user@example.com'},
        'config': job_config_no_priority
    })()
    expected_priority = int(12 + (40 - 12) * 80 / 100)
    assert lab._get_priority(job_human_high_tree) == expected_priority

    job_pipeline_high_tree = type('Job', (), {
        'node': {'data': {'tree_priority': 'high'}, 'submitter': 'service:pipeline'},
        'config': job_config_no_priority
    })()
    expected_priority = int(12 + (40 - 12) * 60 / 100)
    assert lab._get_priority(job_pipeline_high_tree) == expected_priority

    job_medium_tree = type('Job', (), {
        'node': {'data': {'tree_priority': 'medium'}, 'submitter': 'service:pipeline'},
        'config': job_config_no_priority
    })()
    expected_priority = int(12 + (40 - 12) * 40 / 100)
    assert lab._get_priority(job_medium_tree) == expected_priority

    job_low_tree = type('Job', (), {
        'node': {'data': {'tree_priority': 'low'}, 'submitter': 'service:pipeline'},
        'config': job_config_no_priority
    })()
    expected_priority = int(12 + (40 - 12) * 20 / 100)
    assert lab._get_priority(job_low_tree) == expected_priority

    job_default = type('Job', (), {
        'node': {'data': {}, 'submitter': 'service:pipeline'},
        'config': job_config_no_priority
    })()
    expected_priority = int(12 + (40 - 12) * 20 / 100)
    assert lab._get_priority(job_default) == expected_priority

    # Human submission with user-specified string priority
    job_human_set_high = type('Job', (), {
        'node': {'data': {'priority': 'high'}, 'submitter': 'user@example.com'},
        'config': job_config_no_priority
    })()
    expected_priority = int(12 + (40 - 12) * 60 / 100)
    assert lab._get_priority(job_human_set_high) == expected_priority

    # Human submission with user-specified numeric priority
    job_human_set_numeric = type('Job', (), {
        'node': {'data': {'priority': 50}, 'submitter': 'user@example.com'},
        'config': job_config_no_priority
    })()
    expected_priority = int(12 + (40 - 12) * 50 / 100)
    assert lab._get_priority(job_human_set_numeric) == expected_priority


def test_lava_priority_job_config_fallback():
    """Test priority fallback to job.config.priority with string values"""
    config = kernelci.config.load('tests/configs/lava-runtimes.yaml')
    runtimes = config['runtimes']
    runtime_config = runtimes['lab-min-12-max-40-new-runtime']
    lab = kernelci.runtime.get_runtime(runtime_config)

    job_config_medium = type('JobConfig', (), {'priority': 'medium'})()
    job_fallback_str = type('Job', (), {
        'node': {'data': {}, 'submitter': 'service:pipeline'},
        'config': job_config_medium
    })()
    expected_priority = int(12 + (40 - 12) * 40 / 100)
    assert lab._get_priority(job_fallback_str) == expected_priority

    job_config_high = type('JobConfig', (), {'priority': 'high'})()
    job_fallback_high = type('Job', (), {
        'node': {'data': {}, 'submitter': 'service:pipeline'},
        'config': job_config_high
    })()
    expected_priority = int(12 + (40 - 12) * 60 / 100)
    assert lab._get_priority(job_fallback_high) == expected_priority


def test_lava_priority_scale():
    """Test the logic for determining the priority of LAVA jobs"""
    config = kernelci.config.load('tests/configs/lava-runtimes.yaml')
    runtimes = config['runtimes']
    plans = config['test_plans']

    prio_specs = {
        'lab-baylibre': {
            'baseline': 90,
            'baseline-nfs': 85,
        },
        'lab-broonie': {
            'baseline': 40 * 90 / 100,
            'baseline-nfs': 40 * 85 / 100,
        },
        'lab-collabora-staging': {
            'baseline': 45 * 90 / 100,
            'baseline-nfs': 45 * 85 / 100,
        },
        'lab-min-12-max-40': {
            'baseline': 12 + (40 - 12) * 90 / 100,
            'baseline-nfs': 12 + (40 - 12) * 85 / 100,
        },
    }

    for runtime_name, specs in prio_specs.items():
        runtime_config = runtimes[runtime_name]
        priorities = ' '.join(str(prio) for prio in [
            runtime_config.priority,
            runtime_config.priority_min,
            runtime_config.priority_max,
        ])
        print(f"{runtime_name}: {priorities}")
        lab = kernelci.runtime.get_runtime(runtime_config)
        lab.import_devices(f'tests/configs/{runtime_name}.json')
        for plan_name, priority in specs.items():
            plan_config = plans[plan_name]
            lab_priority = lab._get_priority(plan_config)
            spec_priority = int(priority)
            print(f"* {plan_name:12s} {lab_priority:3d} {spec_priority:3d}")
            assert lab_priority == spec_priority


def test_lava_get_devicetype_job_count():
    """Test queued job count via jobs API with state=Submitted."""
    config = kernelci.config.load('tests/configs/lava-runtimes.yaml')
    runtime_config = config['runtimes']['lab-min-12-max-40-new-runtime']
    lab = kernelci.runtime.get_runtime(runtime_config)

    def handler(url, params):
        assert url.endswith('jobs/')
        assert params.get('state') == 'Submitted'
        dev_type = params.get('requested_device_type')
        if dev_type == 'type-a':
            return {'count': 61, 'next': None, 'previous': None, 'results': []}
        if dev_type == 'type-b':
            return {'count': 40, 'next': None, 'previous': None, 'results': []}
        raise AssertionError(f"Unexpected request: {url} {params}")

    lab._server = types.SimpleNamespace(
        url='http://lava/api/v0.2/',
        session=_FakeSession(get_handler=handler),
    )

    counts = lab.get_devicetype_job_count(['type-a', 'type-b'])
    assert counts == {'type-a': 61, 'type-b': 40}


def test_lava_get_device_names_by_type():
    """Test device name lookups with type filtering and health checks."""
    config = kernelci.config.load('tests/configs/lava-runtimes.yaml')
    runtime_config = config['runtimes']['lab-min-12-max-40-new-runtime']
    lab = kernelci.runtime.get_runtime(runtime_config)

    def handler(url, params):
        if url.endswith('devices/'):
            dev_type = params.get('device_type')
            if dev_type == 'type-a':
                return {
                    'results': [
                        {'device_type': 'type-a', 'hostname': 'dev-1', 'health': 'Good'},
                        {'device_type': 'type-a', 'hostname': 'dev-2', 'health': 'Bad'},
                        {'device_type': 'type-b', 'hostname': 'dev-x', 'health': 'Good'},
                    ],
                    'next': None,
                }
            if dev_type == 'type-b':
                return {
                    'results': [
                        {'device_type': 'type-b', 'hostname': 'dev-3', 'health': 'Good'},
                    ],
                    'next': None,
                }
        raise AssertionError(f"Unexpected request: {url} {params}")

    lab._server = types.SimpleNamespace(
        url='http://lava/api/v0.2/',
        session=_FakeSession(get_handler=handler),
    )

    names = lab.get_device_names_by_type('type-a', online_only=True)
    assert names == ['dev-1']

    names_by_type = lab.get_device_names_by_type(['type-a', 'type-b'])
    assert names_by_type == {'type-a': ['dev-1', 'dev-2'], 'type-b': ['dev-3']}


def test_lava_submit_rest():
    """Test LAVA REST submission builds a job with expected payload."""
    config = kernelci.config.load('tests/configs/lava-runtimes.yaml')
    runtime_config = config['runtimes']['lab-min-12-max-40-new-runtime']
    lab = kernelci.runtime.get_runtime(runtime_config)

    captured = {}

    def post_handler(url, payload):
        assert url.endswith('jobs/')
        captured['json'] = payload
        return _FakeResponse({'job_ids': [123]})

    lab._server = types.SimpleNamespace(
        url='http://lava/api/v0.2/',
        session=_FakeSession(post_handler=post_handler),
    )

    job_id = lab._submit("jobdef")
    assert job_id == 123
    assert captured['json']['definition'] == "jobdef"
