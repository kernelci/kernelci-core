#!/usr/bin/python3

import os
from jinja2 import Environment, FileSystemLoader
import re


def env_override(value, key):
    return os.getenv(key, value)


d = os.getenv('DEFCONFIG').split('+')
defconfig = d[0]
frag = None
if len(d) > 1:
    frag = d[1]

job_name = 'build-j{}-{}-{}-{}'.format(
    os.getenv('BUILD_ID'),
    os.getenv('ARCH'),
    os.getenv('BUILD_ENVIRONMENT'),
    defconfig,
)

if frag:
    frag = os.path.splitext(os.path.basename(frag))[0]
    job_name += "-{}".format(frag)

# job name can only have '-'
job_name = re.sub('[\./_+=]', '-', job_name).lower()

# FIXME: needs to be tweaked according to k8s cluster VMs
cpu_limit = 8
parallel_builds = os.getenv('PARALLEL_BUILDS')
if parallel_builds:
    parallel_builds = int(parallel_builds)
    cpu_limit = min(cpu_limit, parallel_builds)
    os.environ['PARALLEL_JOPT'] = "-j{}".format(parallel_builds)
cpu_request = cpu_limit * 0.875

params = {
    'job_name': job_name,
    'cpu_limit': cpu_limit,
    'cpu_request': cpu_request,
}
env = Environment(loader=FileSystemLoader(['.', 'templates', 'templates/k8s']),
                  extensions=["jinja2.ext.do"])
env.filters['env_override'] = env_override
template = env.get_template("job-build.jinja2")
job_yaml = template.render(params)
f = job_name + ".yaml"
fp = open(f, "w")
fp.write(job_yaml)
fp.close()
print(job_name)
