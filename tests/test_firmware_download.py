# SPDX-License-Identifier: LGPL-2.1-or-later
"""Run the generated firmware downloader against a local HTTP fixture."""

import gzip
import http.server
import subprocess
import threading
from pathlib import Path

import pytest
import yaml
from jinja2 import Environment, FileSystemLoader

from kernelci.kbuild import KBuild


@pytest.fixture
def origin():
    """Serve cache and upstream responses independently."""
    firmware = gzip.compress(b"complete firmware archive" * 100)
    state = {
        "cache": firmware,
        "upstream": firmware,
        "cache_status": 200,
        "cache_interrupted": False,
        "requests": [],
    }

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            name = self.path.lstrip("/")
            state["requests"].append(name)
            body = state[name]
            status = state["cache_status"] if name == "cache" else 200
            self.send_response(status)
            extra = 10 if name == "cache" and state["cache_interrupted"] else 0
            self.send_header("Content-Length", str(len(body) + extra))
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    state["url"] = f"http://127.0.0.1:{server.server_port}"
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def download(tmp_path, origin, cache_available=True):
    """Execute the same error trap used by build scripts."""
    build = object.__new__(KBuild)
    build._steps = []
    build.enable_trap()
    build._add_firmware_download()
    script = "stage=2\n" + "\n".join(build._steps)
    script = script.replace(
        "http://tarball-cache/linux-firmware.tar.gz", origin["url"] + "/cache"
    ).replace(
        "https://storage.kernelci.org/linux-firmware.tar.gz",
        origin["url"] + "/upstream",
    )
    script = script.replace(
        "getent hosts tarball-cache", "true" if cache_available else "false"
    )
    # Avoid production retry delays in the HTTP failure fixtures.
    script = script.replace("-t 3", "-t 1").replace("-t 10", "-t 1")
    return subprocess.run(
        ["bash", "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_cache_hit_needs_no_upstream_or_shared_volume(tmp_path, origin):
    result = download(tmp_path, origin)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "linux-firmware.tar.gz").read_bytes() == origin["cache"]
    assert origin["requests"] == ["cache"]


@pytest.mark.parametrize(
    "failure", ["missing", "corrupt", "interrupted", "empty"]
)
def test_bad_cache_response_falls_back_to_complete_upstream(
    tmp_path, origin, failure
):
    if failure == "missing":
        origin["cache_status"] = 404
    elif failure == "corrupt":
        origin["cache"] = origin["cache"][:-8]
    elif failure == "interrupted":
        origin["cache_interrupted"] = True
    else:
        origin["cache"] = b""
    result = download(tmp_path, origin)
    assert result.returncode == 0, result.stderr
    assert origin["requests"] == ["cache", "upstream"]
    assert (tmp_path / "linux-firmware.tar.gz").read_bytes() == origin[
        "upstream"
    ]


def test_cluster_without_cache_downloads_directly(tmp_path, origin):
    result = download(tmp_path, origin, cache_available=False)
    assert result.returncode == 0, result.stderr
    assert origin["requests"] == ["upstream"]


def test_invalid_upstream_never_replaces_existing_complete_file(
    tmp_path, origin
):
    previous = gzip.compress(b"previous complete archive")
    target = tmp_path / "linux-firmware.tar.gz"
    target.write_bytes(previous)
    origin["upstream"] = b"truncated archive"
    result = download(tmp_path, origin, cache_available=False)
    assert result.returncode == 2
    assert target.read_bytes() == previous


def test_new_kubernetes_jobs_have_no_firmware_pvc_dependency():
    templates = Path(__file__).parents[1] / "config" / "runtime"
    template = Environment(loader=FileSystemLoader(templates)).get_template(
        "base/kubernetes.jinja2"
    )
    job = yaml.safe_load(
        template.render(
            k8s_job_name="firmware-http-test",
            runtime_image="kernelci/test:latest",
            k8s_api_key="api-key",
            k8s_storage_token_name="storage-key",
        )
    )
    spec = job["spec"]["template"]["spec"]
    assert all(
        "persistentVolumeClaim" not in volume for volume in spec["volumes"]
    )
    assert all(
        mount["mountPath"] != "/data"
        for container in spec["containers"]
        for mount in container["volumeMounts"]
    )
