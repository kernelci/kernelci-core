import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from kernelci.lab import LabAPI


class Shell(LabAPI):
    BASE_PATH = 'config/scripts'

    def generate(self, params, target_config, plan_config, callback_opts=None,
                 db_config=None, base_path=None):
        jinja2_env = Environment(loader=FileSystemLoader(
            base_path or self.BASE_PATH
        ))
        template_path = plan_config.get_template_path(None)
        template = jinja2_env.get_template(template_path)
        if db_config:
            params['db_config_yaml'] = db_config.to_yaml()
        return template.render(params)

    def job_file_name(self, params):
        return '-'.join([params['node_id'], params['name']])

    def save_file(self, *args, **kwargs):
        output_file = super().save_file(*args, **kwargs)
        os.chmod(output_file, 0o775)
        return output_file

    def submit(self, job_path):
        process = subprocess.Popen(job_path, shell=True)
        return process.pid


def get_api(lab, **kwargs):
    """Get a Shell object"""
    return Shell(lab, **kwargs)
