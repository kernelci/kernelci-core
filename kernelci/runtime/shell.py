# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2021-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

import os
import subprocess
from kernelci.runtime import Runtime


class Shell(Runtime):

    def generate(self, params, device_config, plan_config):
        template = self._get_template(plan_config)
        return template.render(params)

    def save_file(self, *args, **kwargs):
        output_file = super().save_file(*args, **kwargs)
        os.chmod(output_file, 0o775)
        return output_file

    def submit(self, job_path):
        return subprocess.Popen(job_path)


def get_runtime(runtime_config, **kwargs):
    """Get a Shell runtime object"""
    return Shell(runtime_config, **kwargs)
