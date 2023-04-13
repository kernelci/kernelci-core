# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2021-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Shell runtime implementation"""

import os
import subprocess
from . import Runtime


class Shell(Runtime):
    """Runtime implementation to run jobs in a local shell

    The Shell runtime is a simple one to start a subprocess and launch the
    generated script or any executable in it.  It then returns the subprocess
    Popen object so the caller can wait for it to complete and get its output.
    """

    def generate(self, job, params):
        template = self._get_template(job.config)
        return template.render(params)

    def save_file(self, *args, **kwargs):
        output_file = super().save_file(*args, **kwargs)
        os.chmod(output_file, 0o775)
        return output_file

    def submit(self, job_path):
        return subprocess.Popen(job_path)

    def get_job_id(self, job_object):
        return job_object.pid

    def wait(self, job_object):
        job_object.wait()
        return job_object.returncode


def get_runtime(runtime_config, **kwargs):
    """Get a Shell runtime object"""
    return Shell(runtime_config, **kwargs)
