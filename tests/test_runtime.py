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

import kernelci.config
import kernelci.runtime


def test_runtimes_init():
    """Test that all the runtimes can be initialised (offline)"""
    config = kernelci.config.load('tests/configs/runtimes.yaml')
    runtimes = config['runtimes']
    for runtime_name, runtime_config in runtimes.items():
        print(f"Runtime name: {runtime_name}")
        kernelci.runtime.get_runtime(runtime_config)


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
