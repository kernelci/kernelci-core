#!/usr/bin/python

import yaml
import sys
import urllib2


def logfile_url(base, job):
    return ("%s/scheduler/job/%i/log_file/plain" % (base, job))


def results_url(base, job):
    return ("%s/results/%i/yaml" % (base, job))


def definition_url(base, job):
    return ("%s/scheduler/job/%i/definition/plain" % (base, job))


def base_url_from_topic(topic):
    if topic.startswith("http://") or topic.startswith("https://"):
        if topic.endswith(".testjob"):
            return topic[:-8]
        return topic
    else:
        bits = topic.split(".")
        if 'testjob' in bits:
            bits.remove('testjob')
        bits.reverse()
        url = "http://" + ".".join(bits)
        return url


def logfile_parse(logfile):
    final = []
    for line in logfile.splitlines():
        bits = yaml.load(line)[0]
        if bits['lvl'] == 'target':
            final.append(bits['msg'])
    return "\n".join(final)


def fetch(url):
    return urllib2.urlopen(url).read()


def update_api():
    print "Updating kernelci api"
    print "STATUS: %s" % status


data = ""
useful_status = ["complete", "incomplete", "cancelled"]
topic = sys.argv[1]

# http://lava.streamtester.net/scheduler/job/109/log_file/plain
# http://lava.streamtester.net/results/109/yaml
# http://lava.streamtester.net/results/109/metadata
# http://lava.streamtester.net/scheduler/job/109/definition/plain

for line in sys.stdin:
    data += line
try:
    jobinfo = yaml.load(data)
except yaml.YAMLError as exc:
    print exc
    sys.exit(0)

status = jobinfo['status'].lower()
job = int(jobinfo['job'])
base_url = base_url_from_topic(topic)
kernel_messages = []

if status in useful_status:
    logfile_yaml = logfile_parse(fetch(logfile_url(base_url, job)))
    results_yaml = fetch(results_url(base_url, job))
    definition_yaml = fetch(definition_url(base_url, job))
    jobdef = yaml.load(definition_yaml)
    if 'metadata' in jobdef:
        metadata = jobdef['metadata']
    results = yaml.load(results_yaml)
    for result in results:
        if result['name'] == 'auto-login-action':
            if 'metadata' in result:
                if 'extra' in result['metadata']:
                    if 'fail' in result['metadata']['extra']:
                        for fail in result['metadata']['extra']['fail']:
                            kernel_messages.append(fail['message'])
                        print "Kernel error messages:"
                        print "\n".join(kernel_messages)
            kernel_boot_time = result['metadata']['duration']
            print "kernel boot time is: %s seconds" % kernel_boot_time
    update_api()
else:
    print "job still running"
