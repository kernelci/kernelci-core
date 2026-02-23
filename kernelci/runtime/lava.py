# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019 Linaro Limited
# Author: Dan Rue <dan.rue@linaro.org>
#
# Copyright (C) 2019, 2021-2025 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Michal Galka <michal.galka@collabora.com>
# Author: Denys Fedoryshchenko <denys.f@collabora.com>

"""LAVA runtime implementation"""

from collections import namedtuple
import tempfile
import time
import uuid
from urllib.parse import urljoin

import requests
import yaml

from kernelci.runtime import (
    Runtime,
    evaluate_test_suite_result
)


# This will go away when adding get_html_log()
# pylint: disable=too-few-public-methods
class LogParser:
    """LAVA log parser

    This class can be used to parse LAVA logs as received in a callback, in
    YAML format via *log_data_yaml*.  It can then produce a plain text version
    with just the serial output from the test platform.
    """

    def __init__(self, log_data_yaml):
        self._raw_log = self._get_raw_log(log_data_yaml)

    @classmethod
    def _get_raw_log(cls, log_data_yaml):
        log = yaml.safe_load(log_data_yaml)
        raw_log = []
        for line in log:
            dtime, level, msg = (line.get(key) for key in ['dt', 'lvl', 'msg'])
            if not isinstance(msg, str):
                continue
            msg = msg.strip().replace('\x1b', '^[')
            if msg:
                raw_log.append((dtime, level, msg))
        return raw_log

    def get_text_log(self, output):
        """Get the plain text serial console output log from the plaform"""
        for _, level, msg in self._raw_log:
            if level == 'target':
                output.write(msg)
                output.write('\n')

    def get_text(self):
        """Get the plain text serial console output as a string"""
        output = ""
        for _, level, msg in self._raw_log:
            if level == 'target':
                output += msg + '\n'
        return output

    def get_data(self):
        """Get the raw log data as a list of dicts in LAVA output.yaml format"""
        return [{'dt': dt, 'lvl': lvl, 'msg': msg} for dt, lvl, msg in self._raw_log]


class Callback:
    """LAVA callback handler"""

    # copied from lava-server/lava_scheduler_app/models.py
    SUBMITTED = 0
    RUNNING = 1
    COMPLETE = 2
    INCOMPLETE = 3
    CANCELED = 4
    CANCELING = 5

    # LAVA job result names
    LAVA_JOB_RESULT_NAMES = {
        COMPLETE: "pass",
        INCOMPLETE: "incomplete",
        CANCELED: "incomplete",
        CANCELING: "incomplete",
    }

    def __init__(self, data):
        """This class can be used to parse LAVA callback data"""
        self._data = data
        self._meta = None

    def get_data(self):
        """Get the raw callback data"""
        return self._data

    def get_device_id(self):
        """Get the ID of the tested device"""
        return self._data.get('actual_device_id')

    def get_meta(self, key):
        """Get a metadata value from the job definition"""
        if self._meta is None:
            self._meta = yaml.safe_load(self._data['definition'])['metadata']
        return self._meta.get(key)

    def get_job_status(self):
        """Get the job status"""
        # map over LAVA_JOB_RESULT_NAMES
        return self.LAVA_JOB_RESULT_NAMES.get(self._data['status'])

    def is_infra_error(self):
        """Determine wether the job has hit an infrastructure error"""
        lava_yaml = self._data['results']['lava']
        lava = yaml.safe_load(lava_yaml)
        stages = {stage['name']: stage for stage in lava}
        job_meta = stages['job']['metadata']
        return job_meta.get('error_type') == "Infrastructure"

    def _get_job_failure_metadata(self):
        """Get failed lava job metadata fields such as error type and
        error message"""
        lava_yaml = self._data['results'].get('lava')
        if not lava_yaml:
            return None
        lava = yaml.safe_load(lava_yaml)
        stages = {stage['name']: stage for stage in lava}
        job_meta = stages.get('job', {}).get('metadata')
        return job_meta

    @classmethod
    def _get_login_case(cls, tests):
        # When boot has failure_retry set, there may be multiple login attempts
        # We should return 'pass' if ANY attempt passed, 'fail' only if ALL failed
        login_tests = [
            test for test in tests
            if test['name'] in ('auto-login-action', 'login-action')
        ]
        if not login_tests:
            return None

        # Check if any login attempt passed
        any_passed = any(test['result'] == 'pass' for test in login_tests)
        return 'pass' if any_passed else 'fail'

    @classmethod
    def _get_kernelmsg_case(cls, tests):
        # When boot has failure_retry set, there may be multiple kernel-messages checks
        # Unlike login, we return 'fail' if ANY attempt failed, because kernel-messages
        # failure means we caught kernel panic, oops, or other critical errors
        kernelmsg_tests = [
            test for test in tests
            if test['name'] == 'kernel-messages'
        ]
        if not kernelmsg_tests:
            return None

        # Check if any kernel-messages check failed (caught panic/oops/etc)
        any_failed = any(test['result'] == 'fail' for test in kernelmsg_tests)
        return 'fail' if any_failed else 'pass'

    def _get_os_release_measurement(self):
        for suite_name, suite_results in self._data['results'].items():
            if suite_name != '0_tast':
                continue
            tests = yaml.safe_load(suite_results)
            tests_map = {test['name']: test for test in tests}
            os_release = tests_map.get('os-release')
            if os_release:
                return os_release.get('measurement')
        return None

    @classmethod
    def _get_suite_results(cls, tests):
        suite_results = {}
        for test in reversed(tests):
            test_set_name = test['metadata'].get('set')
            if test_set_name:
                test_cases = suite_results.setdefault(test_set_name, {})
            else:
                test_cases = suite_results
            test_cases[test['name']] = test['result']
        return suite_results

    def get_results(self):
        """Parse the results and return them as a plain dictionary"""
        results = {}
        for suite_name, suite_results in self._data['results'].items():
            tests = yaml.safe_load(suite_results)
            if suite_name == 'lava':
                setup = {
                    key: result for key, result in {
                        'login': self._get_login_case(tests),
                        'kernelmsg': self._get_kernelmsg_case(tests)
                    }.items() if result
                }
                if setup:
                    results['setup'] = setup
            else:
                suite_name = suite_name.partition("_")[2]
                results[suite_name] = self._get_suite_results(tests)
        return results

    def _get_stage_result(self, suite_name):
        lava_yaml = self._data['results']['lava']
        lava = yaml.safe_load(lava_yaml)
        stages = {stage['name']: stage for stage in lava}
        result = None
        for stage_name, stage_results in stages.items():
            stage_name = stage_name.partition("_")[2]
            if stage_name == suite_name:
                result = stage_results['result']
        return result

    def _get_results_hierarchy(self, results):
        hierarchy = []
        for name, value in results.items():
            node = {'name': name, 'state': 'done'}
            child_nodes = []
            item = {'node': node, 'child_nodes': child_nodes}
            if isinstance(value, dict):
                item['child_nodes'] = self._get_results_hierarchy(value)
                node['result'] = self._get_stage_result(node['name'])
                if not node['result'] or node['result'] == 'pass':
                    # Sometimes LAVA reports stage result as `pass` even if sub-tests
                    # failed
                    node['result'] = evaluate_test_suite_result(item['child_nodes'])
                node['kind'] = 'job'
            elif isinstance(value, str):
                node['result'] = value
                node['kind'] = 'test'
                if node['name'] == 'os-release':
                    node['data'] = {"misc": {}}
                    node['data']['misc']['measurement'] = self._get_os_release_measurement()
            hierarchy.append(item)
        return hierarchy

    def _get_job_node_result(self, suite_nodes, job_result):
        """ Calculate job node result
        If all child test suites pass, the job will be marked as `pass`
        If one of the test suites fails, the job will be marked as `fail`
        If `setup` test suite fails, it means that the main test suite
        couldn't run and will be marked as `incomplete`
        """
        result = job_result
        for suite in suite_nodes:
            suite = suite['node']
            if suite['result'] == 'fail':
                if suite['name'] == 'setup':
                    result = 'incomplete'
                    break
                result = 'fail'
        return result

    def get_hierarchy(self, results, job_node):
        """Convert the plain results dictionary to a hierarchy for the API"""
        job_result = job_node['result']
        if job_result == "incomplete":
            job_meta = self._get_job_failure_metadata()
            if job_meta:
                job_node['data']['error_code'] = job_meta.get('error_type')
                job_node['data']['error_msg'] = job_meta.get('error_msg')
            else:
                print(f"Job failure metadata not found for node: {job_node['id']}")
                job_node['data']['error_code'] = "Infrastructure"
                job_node['data']['error_msg'] = "Unknown infrastructure error"

        child_nodes = self._get_results_hierarchy(results)

        if job_result == 'incomplete' and 'baseline' in job_node['name']:
            for child in child_nodes:
                if child['node']['name'] == 'setup' and child['node']['result'] == 'fail':
                    print(f"DEBUG: Setup failed for {job_node['id']}. Transitting job node \
result: incomplete -> fail")
                    job_result = 'fail'
                    break

        if job_result == 'pass':
            final_job_result = self._get_job_node_result(child_nodes, job_result)
            if final_job_result != job_result:
                print(f"DEBUG: {job_node['id']} Transitting job node \
result: {job_result} -> {final_job_result}")
                job_result = final_job_result

        return {
            'node': {
                'name': job_node['name'],
                'result': job_result,
                'artifacts': {},
                'data': job_node['data'],
            },
            'child_nodes': child_nodes,
        }

    def get_log_parser(self):
        """Get a LogParser object from the callback data"""
        log = self._data.get('log')
        if not log:
            return None
        return LogParser(log)

    def to_file(self, filename):
        """Write the callback data to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(self._data)


class LAVA(Runtime):
    """Runtime implementation to run jobs in a LAVA lab

    LAVA is a framework for running tests on real hardware or QEMU.  This
    provides the basic features needed to generate a job defintion, submit it
    and wait for the job to complete.

    This currently only supports the REST API v0.2 and doesn't look for online
    devices or aliases.  It also doesn't take into account the callback
    parameters so results can't be sent to the API yet.  It requiers an API
    token to be provided to the constructor.  The user name is not used.
    """
    API_VERSION = 'v0.2'
    RestAPIServer = namedtuple('RestAPIServer', ['url', 'session'])

    # LAVA supports 'high'/'medium'/'low' (100/50/0), but we define our own
    # values to allow scaling across labs with different priority ranges.
    PRIORITY_HIGHEST = 80
    PRIORITY_HIGH = 60
    PRIORITY_MEDIUM = 40
    PRIORITY_LOW = 20

    SERVICE_PIPELINE = 'service:pipeline'

    def __init__(self, configs, kcictx=None, **kwargs):
        super().__init__(configs, **kwargs)
        self._context = kcictx
        self._server = self._connect()

    def _resolve_priority(self, value, default):
        """Resolve a priority value (string, number, or None) to an integer."""
        if value is None:
            return default
        if isinstance(value, str):
            priority_map = {
                'high': self.PRIORITY_HIGH,
                'medium': self.PRIORITY_MEDIUM,
                'low': self.PRIORITY_LOW,
            }
            return priority_map.get(value.lower(), default)
        return max(0, min(100, int(value)))

    def _get_priority(self, job):
        node = job.node
        submitter = node.get('submitter')

        if submitter and submitter != self.SERVICE_PIPELINE:
            user_priority = node.get('data', {}).get('priority')
            priority = self._resolve_priority(
                user_priority, self.PRIORITY_HIGHEST
            )
        else:
            tree_priority = node.get('data', {}).get('tree_priority')
            if tree_priority is not None:
                priority = self._resolve_priority(
                    tree_priority, self.PRIORITY_LOW
                )
            else:
                priority = self._resolve_priority(
                    job.config.priority, self.PRIORITY_LOW
                )

        if self.config.priority:
            priority = int(priority * self.config.priority / 100)
        elif (self.config.priority_max is not None and
              self.config.priority_min is not None):
            prio_range = self.config.priority_max - self.config.priority_min
            prio_min = self.config.priority_min
            priority = int((priority * prio_range / 100) + prio_min)
        return priority

    def get_params(self, job, api_config=None):
        params = super().get_params(job, api_config)
        params['notify'] = self.config.notify
        params['priority'] = self._get_priority(job)
        return params

    def generate(self, job, params):
        template = self._get_template(job.config)
        try:
            rendered = template.render(params)
        # jinja2.exceptions.UndefinedError
        except Exception as exc:  # pylint: disable=broad-except
            raise ValueError(
                f"Error rendering job template: {exc}"
            ) from exc

        # yaml round-trip to process e.g. multi-line commands
        return yaml.dump(yaml.load(rendered, Loader=yaml.CLoader))

    def submit(self, job_path):
        with open(job_path, 'r', encoding='utf-8') as job_file:
            job = job_file.read()
            job_id = self._submit(job)
            return job_id

    def get_job_id(self, job_object):
        job_id = int(job_object)
        return job_id

    def wait(self, job_object):
        job_id = int(job_object)
        job_url = urljoin(self._server.url, '/'.join(['jobs', str(job_id)]))
        while True:
            resp = self._server.session.get(job_url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data['state'] == 'Finished':
                health = data['health']
                return 0 if health == 'Complete' else 1
            time.sleep(3)

    def _connect(self):
        if not hasattr(self.config, 'url') or not self.config.url:
            return self.RestAPIServer(None, None)
        rest_url = f'{self.config.url}/api/{self.API_VERSION}/'
        rest_api = self.RestAPIServer(rest_url, requests.Session())
        rest_api.session.params = {'format': 'json', 'limit': '256'}
        rest_api.session.headers = {
            'authorization': f'Token {self._token}',
            'content-type': 'application/json',
        }
        return rest_api

    def _get_response(self, url, params=None):
        resp = self._server.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _get_all(self, url, params=None):
        resp = self._get_response(url, params=params)
        results = resp.get('results', [])
        next_url = resp.get('next')
        while next_url:
            resp = self._get_response(next_url)
            results.extend(resp.get('results', []))
            next_url = resp.get('next')
        return results

    def get_devicetype_job_count(self, device_types):
        """Get queued job counts per requested device type.

        *device_types* can be a device type name or list of device type names.
        This queries /jobs/?state=Submitted&requested_device_type=<type> and
        reads the 'count' field from the paginated DRF response.
        """
        if self._server.url is None:
            raise ValueError("LAVA server URL is not configured")

        single_type = isinstance(device_types, str)
        if single_type:
            requested_types = [device_types]
        else:
            requested_types = list(device_types or [])
        if not requested_types:
            return 0 if single_type else {}

        jobs_url = urljoin(self._server.url, 'jobs/')
        counts = {}
        for dev_type in requested_types:
            params = {
                'state': 'Submitted',
                'requested_device_type': dev_type,
            }
            resp = self._get_response(jobs_url, params=params)
            counts[dev_type] = resp.get('count', 0)

        if single_type:
            return counts.get(requested_types[0], 0)
        return counts

    def get_device_names_by_type(self, device_type, online_only=False):
        """Get device names for a given LAVA device type.

        *device_type* can be a string or list of device type names.
        *online_only* filters devices with health == 'Good' when available.
        Use this with get_devicetype_job_count() to gate submissions when the
        queue per device type exceeds a threshold.
        """
        if self._server.url is None:
            raise ValueError("LAVA server URL is not configured")

        single_type = isinstance(device_type, str)
        if single_type:
            device_types = [device_type]
        else:
            device_types = list(device_type or [])
        if not device_types:
            return [] if single_type else {}

        devices_url = urljoin(self._server.url, 'devices/')
        result = {}
        for dev_type in device_types:
            params = {'device_type': dev_type}
            devices = self._get_all(devices_url, params=params)
            names = []
            for device in devices:
                if device.get('device_type') != dev_type:
                    continue
                if online_only and device.get('health') not in (None, 'Good'):
                    continue
                hostname = device.get('hostname') or device.get('name')
                if hostname:
                    names.append(hostname)
            result[dev_type] = names
        if single_type:
            return result.get(device_types[0], [])
        return result

    def _submit(self, job):
        if self._server.url is None:
            return self._store_job_in_external_storage(job)

        jobs_url = urljoin(self._server.url, 'jobs/')
        job_data = {
            'definition': job,
        }
        resp = self._server.session.post(
            jobs_url, json=job_data, allow_redirects=False,
            timeout=30,
        )
        if resp.status_code >= 400:
            print(f"Error submitting job: {resp.status_code}, {resp.text}")
        resp.raise_for_status()
        return resp.json()['job_ids'][0]

    def _store_job_in_external_storage(self, job):
        """Store job in external storage when LAVA server URL is not defined"""
        storage, storage_name = self._get_storage_config(self._context)

        date_str = time.strftime("%Y%m%d")
        unique_id = uuid.uuid4().hex
        upload_path = f"/jobs/{date_str}/{unique_id}.yaml"
        print(f"Storing def '{storage_name}' path: {upload_path} name: {unique_id}.yaml")
        stored_url = None
        # Store the job definition in external storage
        try:
            job_bytes = job.encode('utf-8')
            with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
                tmp_file.write(job_bytes)
                tmp_file.flush()
                local_file = tmp_file.name
                artifact_name = f"{unique_id}.yaml"
                stored_url = storage.upload_single(
                    (local_file, artifact_name), upload_path,
                )
                self._stored_url = stored_url

            if not self._stored_url:
                raise ValueError("Upload returned no URL")
            print(f"Job stored at URL: {stored_url}")
        except Exception as exc:
            raise ValueError(f"Failed to store job in external storage: {exc}") from exc


def get_runtime(runtime_config, **kwargs):
    """Get a LAVA runtime object"""
    return LAVA(runtime_config, **kwargs)
