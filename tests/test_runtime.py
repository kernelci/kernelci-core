# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019 Linaro Limited
# Author: Dan Rue <dan.rue@linaro.org>
#
# Copyright (C) 2019, 2021, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

import json

import kernelci.config
import kernelci.lab

def test_lava_priority_scale():
    config = kernelci.config.load('tests/configs/runtime.yaml')
    labs = config['labs']
    plans = config['test_plans']

    prio_specs = {
        'lab-baylibre': {
            'baseline': 90,
            'baseline-nfs': 85,
        },
        'lab-broonie-min-max': {
            'baseline': 12 + (40 - 12) * 90 / 100,
            'baseline-nfs': 12 + (40 - 12) * 85 / 100,
        },
        'lab-collabora-staging': {
            'baseline': 45 * 90 / 100,
            'baseline-nfs': 45 * 85 / 100,
        },
    }

    for lab_name, specs in prio_specs.items():
        lab_config = labs[lab_name]
        print("{}: {} {} {}".format(
            lab_name, lab_config.priority,
            lab_config.priority_min, lab_config.priority_max
        ))
        lab = kernelci.lab.get_api(
            lab_config, lab_json=f'tests/configs/{lab_name}.json'
        )
        for plan_name, priority in specs.items():
            plan_config = plans[plan_name]
            lab_priority = lab._get_priority(plan_config)
            spec_priority = int(priority)
            print(f"* {plan_name:12s} {lab_priority:3d} {spec_priority:3d}")
            assert lab_priority == spec_priority
