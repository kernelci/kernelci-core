import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from kernelci.lab import LabAPI


class Shell(LabAPI):

    def generate(self, params, device_config, plan_config,
                 callback_opts=None, templates_path='config/scripts'):
        jinja2_env = Environment(loader=FileSystemLoader(templates_path))
        template_path = plan_config.get_template_path(None)
        template = jinja2_env.get_template(template_path)
        return template.render(params)

    def save_file(self, *args, **kwargs):
        output_file = super().save_file(*args, **kwargs)
        os.chmod(output_file, 0o775)
        return output_file

    def submit(self, job_path, get_process=False):
        process = subprocess.Popen(job_path)
        return process if get_process else process.pid


def get_api(lab, **kwargs):
    """Get a Shell object"""
    return Shell(lab, **kwargs)
