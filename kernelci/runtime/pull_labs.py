# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2025 Collabora Limited
# Author: Denys Fedoryshchenko <denys.f@collabora.com>

"""PULL_LABS runtime implementation"""

import base64
import gzip
import json
import tempfile
import time
import uuid

from kernelci.runtime import Runtime, evaluate_test_suite_result


class LogParser:
    """PULL_LABS log parser

    This class can be used to parse PULL_LABS logs as received in a callback.
    It can handle both base64-encoded (optionally gzipped) logs and plain text.
    """

    def __init__(self, log_data):
        """Initialize log parser with log data

        *log_data* can be:
        - base64-encoded string (with optional "base64:" prefix)
        - plain text string
        - gzipped and base64-encoded (prefix "base64:" expected)
        """
        self._raw_log = self._decode_log(log_data)

    @classmethod
    def _decode_log(cls, log_data):
        """Decode log data from various formats"""
        if not log_data:
            return ""

        # Handle base64 encoding
        if isinstance(log_data, str) and log_data.startswith("base64:"):
            try:
                encoded_data = log_data[7:]  # Remove 'base64:' prefix
                decoded_bytes = base64.b64decode(encoded_data)
                # Try to decompress if it's gzipped
                try:
                    decompressed = gzip.decompress(decoded_bytes)
                    return decompressed.decode("utf-8", errors="replace")
                except gzip.BadGzipFile:
                    # Not gzipped, just decode as UTF-8
                    return decoded_bytes.decode("utf-8", errors="replace")
            except Exception as exc:  # pylint: disable=broad-except
                print(f"Warning: Failed to decode base64 log: {exc}")
                return log_data

        # Plain text
        return log_data

    def get_text(self):
        """Get the plain text log as a string"""
        return self._raw_log

    def get_text_log(self, output):
        """Write the plain text log to output"""
        output.write(self._raw_log)


class Callback:
    """PULL_LABS callback handler

    Parses callback data according to PULL_LABS protocol Section 6 & 7.
    """

    # Test result status mapping from PULL_LABS to KernelCI
    STATUS_MAP = {
        "ok": "pass",
        "pass": "pass",
        "fail": "fail",
        "skip": "skip",
        "error": "incomplete",
    }

    def __init__(self, data):
        """Initialize callback handler with callback data

        *data* is the parsed JSON callback data from the lab
        """
        self._data = data

    def get_data(self):
        """Get the raw callback data"""
        return self._data

    def get_device_id(self):
        """Get the ID of the tested device from metadata"""
        metadata = self._data.get("metadata", {})
        return metadata.get("system")

    def get_job_status(self):
        """Get overall job status from summary

        Returns 'pass', 'fail', or 'incomplete' based on test results
        """
        summary = self._data.get("summary", {})
        total = summary.get("total", 0)
        failed = summary.get("failed", 0)

        # If no tests ran, it's incomplete
        if total == 0:
            return "incomplete"

        # If any test failed, overall status is fail
        if failed > 0:
            return "fail"

        return "pass"

    def is_infra_error(self):
        """Determine whether the job has hit an infrastructure error

        Infrastructure errors are indicated by error_code in metadata
        or certain test statuses
        """
        # Check for error_code in top-level data or metadata
        if "error_code" in self._data:
            return True

        metadata = self._data.get("metadata", {})
        if "error_code" in metadata:
            return True

        # Check if all tests have 'error' status
        tests = self._data.get("tests", {})
        if tests:
            all_errors = all(
                self._get_test_status(test) == "error"
                for test in tests.values()
                if isinstance(test, dict)
            )
            return all_errors

        return False

    @classmethod
    def _get_test_status(cls, test_data):
        """Extract status from test data"""
        if isinstance(test_data, dict):
            return test_data.get("status", "error")
        return "error"

    @classmethod
    def _convert_status(cls, status):
        """Convert PULL_LABS status to KernelCI status"""
        return cls.STATUS_MAP.get(status, "incomplete")

    def _parse_test_node(self, name, test_data):
        """Parse a single test node into KernelCI format

        Returns a dict with 'node' and 'child_nodes' keys
        """
        node = {
            "name": name,
            "state": "done",
        }

        # Extract status
        if isinstance(test_data, dict):
            status = test_data.get("status", "error")
            node["result"] = self._convert_status(status)

            # Extract duration if present
            duration_ms = test_data.get("duration_ms")
            if duration_ms is not None:
                node["data"] = node.get("data", {})
                node["data"]["duration_ms"] = duration_ms

            # Extract metrics if present
            metrics = test_data.get("metrics")
            if metrics:
                node["data"] = node.get("data", {})
                node["data"]["metrics"] = metrics

            # Check for subtests
            subtests = test_data.get("subtests", {})
            if subtests:
                node["kind"] = "job"
                child_nodes = self._parse_tests_hierarchy(subtests)

                # Re-evaluate result based on children if needed
                if node["result"] == "pass":
                    child_result = evaluate_test_suite_result(child_nodes)
                    if child_result != node["result"]:
                        node["result"] = child_result

                return {"node": node, "child_nodes": child_nodes}

            # Leaf test node
            node["kind"] = "test"
            return {"node": node, "child_nodes": []}

        # Simple status string
        node["result"] = "incomplete"
        node["kind"] = "test"
        return {"node": node, "child_nodes": []}

    def _parse_tests_hierarchy(self, tests):
        """Parse tests dictionary into hierarchy format"""
        hierarchy = []
        for name, test_data in tests.items():
            item = self._parse_test_node(name, test_data)
            hierarchy.append(item)
        return hierarchy

    def get_results(self):
        """Parse the results and return them as a plain dictionary"""
        return self._data.get("tests", {})

    def get_hierarchy(self, results, job_node):  # pylint: disable=unused-argument
        """Convert the plain results dictionary to a hierarchy for the API

        *results* is the tests dictionary from the callback
        *job_node* is the job node data with initial status
        """
        job_result = job_node.get("result", self.get_job_status())

        # Handle infrastructure errors
        if self.is_infra_error():
            job_result = "incomplete"
            if "data" not in job_node:
                job_node["data"] = {}
            job_node["data"]["error_code"] = self._data.get(
                "error_code", "Infrastructure"
            )
            job_node["data"]["error_msg"] = self._data.get(
                "error_msg", "Infrastructure error"
            )

        # Parse test hierarchy
        tests = self._data.get("tests", {})
        child_nodes = self._parse_tests_hierarchy(tests)

        # Re-evaluate job result based on children
        if child_nodes and job_result == "pass":
            child_result = evaluate_test_suite_result(child_nodes)
            if child_result != job_result:
                print(
                    f"DEBUG: {job_node.get('id')} Transitting job node "
                    f"result: {job_result} -> {child_result}"
                )
                job_result = child_result

        return {
            "node": {
                "name": job_node["name"],
                "result": job_result,
                "artifacts": {},
                "data": job_node.get("data", {}),
            },
            "child_nodes": child_nodes,
        }

    def get_log_parser(self):
        """Get a LogParser object from the callback data"""
        artifacts = self._data.get("artifacts", {})
        log = artifacts.get("log")
        if not log:
            return None
        return LogParser(log)


class PullLabs(Runtime):
    """Runtime implementation for PULL_LABS protocol

    PULL_LABS is a pull-based protocol where external hardware labs poll for
    events, download job definitions, run tests, and post results via callback.

    This runtime generates JSON job definitions according to the PULL_LABS
    protocol specification (Section 3) and handles result callbacks.
    """

    def __init__(self, config, kcictx=None, **kwargs):
        super().__init__(config, **kwargs)
        self._context = kcictx

    def get_params(self, job, api_config=None):
        """Get job template parameters with PULL_LABS-specific additions"""
        params = super().get_params(job, api_config)
        params["timeout"] = self.config.timeout
        params["poll_interval"] = self.config.poll_interval
        return params

    def generate(self, job, params):
        """Generate PULL_LABS job definition in JSON format

        *job* is a Job object
        *params* is the template parameters dictionary

        Returns JSON string of the job definition
        """
        template = self._get_template(job.config)
        try:
            rendered = template.render(params)
            # Validate JSON
            json.loads(rendered)
            return rendered
        except json.JSONDecodeError as exc:
            print(f"Error: Generated template is not valid JSON: {exc}")
            return None
        except Exception as exc:  # pylint: disable=broad-except
            platform_params = (
                params["platform_config"].params
                if params.get("platform_config")
                else {}
            )
            print(
                f"Error rendering job template: {exc}, params: {params}, "
                f"platform_params: {platform_params}"
            )
            return None

    def submit(self, job_path):
        """Store job definition in external storage for pull-based labs

        For PULL_LABS, "submit" means:
        1. Store job definition JSON in external storage
        2. Let the scheduler update the job node to make it available for labs

        *job_path* is the path to the generated job definition file

        Returns ``None`` as pull-based labs pick up jobs asynchronously.
        """
        with open(job_path, "r", encoding="utf-8") as job_file:
            job_definition = job_file.read()
            self._store_job_definition(job_definition)
            return None

    def get_job_id(self, job_object):
        """Extract job ID from the job object returned by submit()"""
        # For PULL_LABS, job_object is already the job ID string
        return str(job_object)

    def wait(self, job_object):
        """Wait for job completion via callback

        For PULL_LABS protocol, jobs complete when the lab posts results
        to the callback endpoint. This method would typically poll the API
        for job state changes.

        *job_object* is the job ID

        Returns 0 for success, 1 for failure

        Note: In practice, this is handled by the pipeline/callback system,
        so this method may not be actively used.
        """
        # In PULL_LABS, waiting is typically handled by the callback system
        # This is a placeholder for compatibility with the Runtime interface
        print(
            f"PULL_LABS: Job {job_object} submitted. "
            "Waiting for lab to accept and complete via callback."
        )

        # For now, return success as the submission itself succeeded
        # Actual job tracking happens via the callback system
        return 0

    def _store_job_definition(self, job_definition):
        """Store job definition in external storage

        *job_definition* is the JSON string of the job definition

        Returns a unique job ID
        """
        # Get storage configuration
        config_storage_name = getattr(self.config, 'storage_name', None)
        storage, storage_name = self._get_storage_config(self._context, config_storage_name)

        # Generate unique ID and path
        date_str = time.strftime("%Y%m%d")
        unique_id = uuid.uuid4().hex
        upload_dir = f"pull_labs_jobs/{date_str}"

        print(
            f"Storing PULL_LABS job definition to '{storage_name}' "
            f"path: {upload_dir} name: {unique_id}.json"
        )

        try:
            job_bytes = job_definition.encode("utf-8")
            with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
                tmp_file.write(job_bytes)
                tmp_file.flush()
                local_file = tmp_file.name
                artifact_name = f"{unique_id}.json"
                stored_url = storage.upload_single(
                    (local_file, artifact_name),
                    upload_dir,
                )
                self._stored_url = stored_url

            if not self._stored_url:
                raise ValueError("Upload returned no URL")

            print(f"Job definition stored at URL: {stored_url}")
            return unique_id

        except Exception as exc:
            raise ValueError(
                f"Failed to store job definition in external storage: {exc}"
            ) from exc


def get_runtime(runtime_config, **kwargs):
    """Get a PULL_LABS runtime object"""
    return PullLabs(runtime_config, **kwargs)
