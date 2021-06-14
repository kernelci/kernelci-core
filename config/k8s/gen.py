#!/usr/bin/env python3

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
job_name = re.sub('[\./_+=:]', '-', job_name).lower()

# k8s limits job-name to max 63 chars (and be sure it doesn't end with '-')
job_name = job_name[0:63].rstrip('-')

# FIXME: needs to be tweaked according to k8s cluster VMs
cpu_limit = int(os.getenv('K8S_CPU_LIMIT', 8))
parallel_builds = os.getenv('PARALLEL_BUILDS')
if parallel_builds:
    parallel_builds = int(parallel_builds)
    cpu_limit = min(cpu_limit, parallel_builds)
    os.environ['PARALLEL_JOPT'] = "{}".format(parallel_builds)

if (cpu_limit < 8):
    cpu_request = cpu_limit * 0.875
# HACK: Azure nodes with 32 vCPUs refuse jobs with
#       CPU request > 30.  Support ticket open with
#       Azure
elif (cpu_limit == 32):
    cpu_request = 30
else:
    cpu_request = cpu_limit - 0.9

# VMs are generous, let's be greedy and ask for 1Gb per core :)
mem_request = cpu_limit

params = {
    'job_name': job_name,
    'cpu_limit': cpu_limit,
    'cpu_request': cpu_request,
    'mem_request': "{}Gi".format(mem_request)
}
env = Environment(loader=FileSystemLoader(['config/k8s']),
                  extensions=["jinja2.ext.do"])
env.filters['env_override'] = env_override
template = env.get_template("job-build.jinja2")
job_yaml = template.render(params)
f = job_name + ".yaml"
fp = open(f, "w")
fp.write(job_yaml)
fp.close()
print(job_name)
