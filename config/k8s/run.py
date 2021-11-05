#!/usr/bin/env python3

import os
import sys
import time
import argparse
import yaml
from kubernetes import client, config, utils, watch
from pprint import pprint
from jinja2 import Environment, FileSystemLoader
import re

def env_override(value, key):
    return os.getenv(key, value)

def job_create(yaml_output, namespace):
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
    job_name = re.sub('[\.:/_+=]', '-', job_name).lower()

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
    job_yaml_text = template.render(params)

    if (yaml_output):
        print("Writing job to ".format(yaml_output))
        fp = open(yaml_output, "w")
        fp.write(job_yaml_text)
        fp.close()

    # Translate the parsed YAML into a k8s job
    job_dict = yaml.safe_load(job_yaml_text)
    try:
        k8s_client = client.ApiClient()
        job = utils.create_from_dict(k8s_client, data=job_dict,
                               namespace=namespace)
    except utils.FailToCreateError as e:
        print("Failed to create job: ", e)
        sys.exit(1)

    print("Started job {}".format(job_name))

    return job_name


def job_show(job):
    print("Succeeded:", job.status.succeeded)
    print("Failed:", job.status.failed)
    if job.status.conditions:
        for cond in job.status.conditions:
            print("condition.type:", cond.type)


def job_succeeded(job):
    return job.status.succeeded == True


def context_valid(c):
    valid = False

    print("Available contexts:")
    contexts, active_context = config.list_kube_config_contexts()
    for ctx in contexts:
        print("   {}".format(ctx['name']))
        if c == ctx['name']:
            valid = True

    return valid

def main(args):
    build_success = True
    k8s_success = True
    job_found = False
    sleep_secs = args.sleep

    if not context_valid(args.context):
        print("ERROR: unknown context", args.context)
        sys.exit(1)

    retries = 3
    print("Using context:", args.context)
    while retries:
        try:
            config.load_kube_config(context=args.context)
            break
        except (TypeError, config.ConfigException) as e:
            print("WARNING: unable to load context {}: {}.  Retrying.".format(args.context, e))
            time.sleep(sleep_secs)
            retries = retries - 1
    if retries == 0:
        print("ERROR: unable to load context {}.  Giving up.".format(args.context))
        sys.exit(1)

    core = client.CoreV1Api()
    batch = client.BatchV1Api()

    job_name = job_create(yaml_output=args.yaml, namespace=args.namespace)

    print("Waiting for job completion.")

    #
    # wait for job to finish
    #
    w = watch.Watch()
    for event in w.stream(batch.list_namespaced_job,
                          label_selector=("job-name=="+job_name),
                          namespace=args.namespace):
        event_job_name = event['object'].metadata.name
        print("Event: %s %s" % (event['type'], event_job_name))

        # Don't explode if we got the label_selector wrong...
        if event_job_name != job_name:
            continue

        # Job finished?
        job = event['object']
        if job.status.completion_time:
            print("%s finished at %s".format(job_name,
                                             job.status.completion_time))
            build_success = job_succeeded(job)
            if build_success:
                print("PASS")
            else:
                print("FAIL")
            if job.status.conditions:
                print("Reason:", job.status.conditions[0].reason)
            else:
                print("Reason: Unknown: job status:")
                pprint(job.status)
            w.stop()

    #
    # Find pod where job ran
    #
    pod = core.list_namespaced_pod(namespace=args.namespace, watch=False,
                                   label_selector="job-name={}".format(job_name))
    if len(pod.items) < 1:
        print("WARNING: no pods found with job name {}".format(job_name))
        sys.exit(0)
    if len(pod.items) > 1:
        print("WARNING: >1 pod found with job name {}".format(job_name))
        sys.exit(0)
    pod_name = pod.items[0].metadata.name
    print("Found job on pod {}".format(pod_name))

    #
    # Get logs (from pod)
    #

    # default: check the main container logs
    cont_name = pod.items[0].spec.containers[0].name

    # unless the initContainer failed, get that log, because if the
    # initContainer failed, the main container will not have run
    if (pod.items[0].spec.init_containers):
        init_cont_name = pod.items[0].spec.init_containers[0].name
        if not pod.items[0].status.init_container_statuses[0].ready:
            print("ERROR: initContainer {} not ready / failed.".format(init_cont_name))
            cont_name = init_cont_name
            k8s_success = False
    try:
        log = core.read_namespaced_pod_log(name=pod_name,
                                           namespace=args.namespace,
                                           container=cont_name)
        print("Container Log:")
        print(log)
    except client.rest.ApiException as e:
        print("Exception: Unable to get pod log", e)
        k8s_success = False

    #
    # Delete job
    #
    if args.delete and k8s_success:
        # important: propagation_policy is important so any pods
        # created for a job deleted
        body = client.V1DeleteOptions(propagation_policy="Foreground")
        ret = batch.delete_namespaced_job(name=job_name,
                                          namespace=args.namespace,
                                          body=body)
        print("job {} deleted.  job.status:".format(job_name))
        pprint(ret.status)

    # Make jenkins fail only if k8s fails.  Kernel build fails will
    # be reported to the backend/
    sys.exit(not k8s_success)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--context')
    parser.add_argument('--save-yaml', dest='yaml', default=None)
    parser.add_argument('--namespace', default='default')
    parser.add_argument('--sleep', type=int, default=60)
    parser.add_argument('--no-delete', dest='delete', default=True, action='store_false')
    args = parser.parse_args()
    main(args)
