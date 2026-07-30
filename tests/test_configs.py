# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019 Linaro Limited
# Author: Dan Rue <dan.rue@linaro.org>
#
# Copyright (C) 2019, 2021, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Unit test for KernelCI YAML config handling"""

import copy

import pytest
import yaml
from pydantic import ValidationError

import kernelci.config
import kernelci.config.build
from kernelci.config.job import Job, JobConfig

# -----------------------------------------------------------------------------
# Legacy
#


def test_build_configs_parsing_minimal():
    """Test that minimal build configs can be parsed from YAML"""
    data = kernelci.config.load_yaml("tests/configs/builds-minimal.yaml")
    configs = kernelci.config.build.from_yaml(data, {})
    assert "agross" in configs["build_configs"]
    assert "agross" in configs["trees"]
    assert "gcc-7" in configs["build_environments"]
    assert len(configs["fragments"]) == 0


def test_build_configs_parsing_empty_architecture():
    """Test that build configs with empty architectures can be parsed"""
    data = kernelci.config.load_yaml("tests/configs/builds-empty-arch.yaml")
    configs = kernelci.config.build.from_yaml(data, {})
    assert len(configs) == 4


def test_architecture_init_name_only():
    """Test that build config objects can be created with just a name"""
    architecture = kernelci.config.build.Architecture("arm")
    assert architecture.name == "arm"
    assert architecture.base_defconfig == "defconfig"
    assert len(architecture.extra_configs) == 0
    assert len(architecture.fragments) == 0
    assert len(architecture._filters) == 0


class ConfigTest:
    """Base class with helpers for all YAML configuration tests"""

    @classmethod
    def _load_config(cls, yaml_file_path):
        with open(yaml_file_path, encoding="utf-8") as yaml_file:
            ref_data = yaml.safe_load(yaml_file)
        config = kernelci.config.load(yaml_file_path)
        return ref_data, config

    @classmethod
    def _reload(cls, ref_data, config, name):
        assert name in config
        assert name in ref_data
        dump = yaml.dump(config[name])
        loaded = yaml.safe_load(dump)
        assert ref_data[name] == loaded
        return loaded


class TestBuildConfigs(ConfigTest):
    """Tests for configs related to builds"""

    def test_trees(self):
        """Test the tree configs"""
        ref_data, config = self._load_config("tests/configs/trees.yaml")
        trees_config = self._reload(ref_data, config, "trees")
        tree_names = ["kselftest", "mainline", "next"]
        assert all(name in ref_data["trees"] for name in tree_names)
        assert all(name in trees_config for name in tree_names)
        assert (
            trees_config["next"]["url"]
            == "https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git"  # noqa
        )

    def test_fragments(self):
        """Test the fragments configs"""
        ref_data, config = self._load_config("tests/configs/fragments.yaml")
        frag_config = self._reload(ref_data, config, "fragments")
        frag_names = ["debug", "ima", "x86-board", "x86_kvm_guest"]
        assert all(name in ref_data["fragments"] for name in frag_names)
        assert all(name in frag_config for name in frag_names)
        assert frag_config["debug"]["path"] == "kernel/configs/debug.config"

    def test_build_environments(self):
        """Test the build_environments configs"""
        ref_data, config = self._load_config(
            "tests/configs/build-environments.yaml"
        )
        be_config = self._reload(ref_data, config, "build_environments")
        be_names = ["gcc-10", "clang-11", "clang-12", "rustc-1.62"]
        assert all(name in ref_data["build_environments"] for name in be_names)
        assert all(name in be_config for name in be_names)
        assert be_config["clang-12"]["cc_version"] == "12"
        clang12 = config["build_environments"]["clang-12"]
        assert (
            clang12.get_arch_param("arm64", "cross_compile_compat")
            == "arm-linux-gnueabihf-"
        )
        assert clang12.get_arch_param("riscv", "opts")["LLVM_IAS"] == "1"

    def test_reference_tree(self):
        """Test the build_configs reference tree configs"""
        ref_data, config = self._load_config("tests/configs/builds.yaml")
        assert "build_configs" in ref_data
        build_configs = ref_data["build_configs"]
        assert "arm64" in build_configs
        arm64 = build_configs["arm64"]
        assert "reference" in arm64
        reference = arm64["reference"]
        reference_config = config["build_configs"]["arm64"].reference
        assert reference_config.tree.name == "mainline"
        reference_dump = yaml.dump(reference_config)
        reference_check = yaml.safe_load(reference_dump)
        assert reference == reference_check

    def test_build_configs(self):
        """Test the build_configs"""
        ref_data, config = self._load_config("tests/configs/builds.yaml")
        build_configs = self._reload(ref_data, config, "build_configs")
        config_names = ["arm64", "mainline"]
        assert all(name in ref_data["build_configs"] for name in config_names)
        assert all(name in build_configs for name in config_names)
        assert build_configs["mainline"]["tree"] == "mainline"


class TestTestConfigs(ConfigTest):
    """Tests for configs related to runtime tests"""

    def test_file_system_types(self):
        """Test the file_system_types configs"""
        ref_data, config = self._load_config(
            "tests/configs/file-system-types.yaml"
        )
        fs_config = self._reload(ref_data, config, "file_system_types")
        fs_names = ["buildroot", "debian"]
        assert all(name in ref_data["file_system_types"] for name in fs_names)
        assert all(name in fs_config for name in fs_names)
        assert (
            fs_config["debian"]["url"]
            == "http://storage.kernelci.org/images/rootfs/debian"
        )


# -----------------------------------------------------------------------------
# API & Pipeline
#


class TestJobConfigs(ConfigTest):
    """Tests for pipeline job definitions"""

    def test_jobs(self):
        """Test the job configs"""
        ref_data, config = self._load_config("tests/configs/jobs.yaml")
        jobs = self._reload(ref_data, config, "jobs")
        job_names = ["kbuild-gcc-10-x86", "kunit", "kunit-x86_64", "kver"]
        assert all(name in ref_data["jobs"] for name in job_names)
        assert all(name in jobs for name in job_names)
        assert (
            jobs["kunit-x86_64"]["image"]
            == "kernelci/staging-gcc-10:x86-kunit-qemu-kernelci"
        )

    def test_job_schema_is_authoritative(self):
        """Expose and serialize schema fields without per-field properties."""
        schema = JobConfig(
            template="kbuild.jinja2",
            kind="kbuild",
            base_name="kbuild-base",
            priority="high",
        )
        job = Job("kbuild-example", config=schema)

        serialized = yaml.safe_load(yaml.dump(job))

        assert set(serialized) == set(JobConfig.model_fields)
        assert serialized["base_name"] == job.base_name
        assert serialized["priority"] == job.priority
        delegated_fields = {
            "template",
            "kind",
            "base_name",
            "rules",
            "kcidb_test_suite",
            "priority",
        }
        assert delegated_fields.isdisjoint(Job.__dict__)

    def test_job_legacy_constructor_uses_schema(self):
        """Keep direct construction compatible while validating its fields."""
        job = Job(
            "legacy-job",
            "kbuild.jinja2",
            kind="kbuild",
            priority="medium",
        )

        assert job.template == "kbuild.jinja2"
        assert job.kind == "kbuild"
        assert job.priority == "medium"
        with pytest.raises(ValidationError, match="unknown"):
            Job(
                "invalid-job",
                template="kbuild.jinja2",
                unknown="value",
            )

    def test_job_image_override_is_runtime_state(self):
        """Keep image overrides separate from immutable source configuration."""
        schema = JobConfig(
            template="kbuild.jinja2",
            image="original:image",
        )
        job = Job("kbuild-example", config=schema)

        job.image = "override:image"

        assert schema.image == "original:image"
        assert job.image == "override:image"
        assert yaml.safe_load(yaml.dump(job))["image"] == "override:image"
        job.image = None
        assert job.image is None

    def test_jobs_reject_unknown_fields(self):
        """Reject misspelled or unsupported job fields."""
        data = {
            "jobs": {
                "broken-job": {
                    "template": "kbuild.jinja2",
                    "temlate": "misspelled.jinja2",
                }
            }
        }

        with pytest.raises(ValidationError, match="temlate"):
            kernelci.config.load_data(data)

    def test_jobs_require_template(self):
        """Require every job to select a template."""
        data = {"jobs": {"broken-job": {"kind": "test"}}}

        with pytest.raises(ValidationError, match="template"):
            kernelci.config.load_data(data)

    @pytest.mark.parametrize("priority", ["low", "medium", "high", 0, 50, 100])
    def test_jobs_accept_supported_priorities(self, priority):
        """Accept symbolic and numeric priorities used by pipeline jobs."""
        data = {
            "jobs": {
                "example": {
                    "template": "kbuild.jinja2",
                    "priority": priority,
                }
            }
        }

        config = kernelci.config.load_data(data)

        assert config["jobs"]["example"].priority == priority

    def test_jobs_preserve_base_name(self):
        """Preserve the base job name used by pipeline job variants."""
        data = {
            "jobs": {
                "ltp-timers_qemu": {
                    "template": "ltp.jinja2",
                    "base_name": "ltp-timers",
                }
            }
        }

        config = kernelci.config.load_data(data)

        job = config["jobs"]["ltp-timers_qemu"]
        assert job.base_name == "ltp-timers"
        assert yaml.safe_load(yaml.dump(job))["base_name"] == "ltp-timers"

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("params", []),
            ("priority", "50"),
            ("priority", 101),
        ],
    )
    def test_jobs_reject_invalid_field_values(self, field, value):
        """Reject invalid job field types and values."""
        data = {
            "jobs": {
                "broken-job": {
                    "template": "kbuild.jinja2",
                    field: value,
                }
            }
        }

        with pytest.raises(ValidationError, match=field):
            kernelci.config.load_data(data)

    def test_jobs_do_not_mutate_source_data(self):
        """Formatting job parameters must not mutate loaded YAML data."""
        data = {
            "jobs": {
                "example": {
                    "template": "kbuild.jinja2",
                    "params": {
                        "arch": "arm64",
                        "nested": {"artifact": "{arch}/kernel"},
                    },
                }
            }
        }
        original = copy.deepcopy(data)

        config = kernelci.config.load_data(data)

        assert data == original
        assert config["jobs"]["example"].params["nested"]["artifact"] == (
            "arm64/kernel"
        )
        returned_params = config["jobs"]["example"].params
        returned_params["nested"]["artifact"] = "modified"
        assert config["jobs"]["example"].params["nested"]["artifact"] == (
            "arm64/kernel"
        )

    def test_jobs_validate_after_config_merge(self, tmp_path):
        """Allow partial overrides by validating after all files are merged."""
        base = tmp_path / "base.yaml"
        overlay = tmp_path / "overlay.yaml"
        base.write_text(
            """
jobs:
  example:
    template: kbuild.jinja2
    params:
      arch: arm64
""",
            encoding="utf-8",
        )
        overlay.write_text(
            """
jobs:
  example:
    priority: 50
""",
            encoding="utf-8",
        )

        config = kernelci.config.load([str(base), str(overlay)])

        assert config["jobs"]["example"].template == "kbuild.jinja2"
        assert config["jobs"]["example"].priority == 50


class TestAPIConfigs(ConfigTest):
    """Tests for configs related to the KernelCI API"""

    def test_apis(self):
        """Test the api configs"""
        ref_data, config = self._load_config("tests/configs/api-configs.yaml")
        api_config = self._reload(ref_data, config, "api")
        api_names = ["docker-host"]
        assert all(name in ref_data["api"] for name in api_names)
        assert all(name in api_config for name in api_names)
        assert api_config["docker-host"]["url"] == "http://172.17.0.1:8001"


class TestRuntimeConfigs(ConfigTest):
    """Tests related to runtime configs"""

    def test_lava_runtime(self):
        """Test the LAVA runtime configs"""
        _, config = self._load_config("tests/configs/lava-runtimes.yaml")
        runtimes = config["runtimes"]
        lava_lab_prio = {
            "lab-baylibre": (None, None, None),
            "lab-broonie": (None, 0, 40),
            "lab-collabora-staging": (45, 45, 45),
            "lab-min-12-max-40": (None, 12, 40),
        }
        assert all(name in runtimes for name, _ in lava_lab_prio.items())
        for lab_name, (fixed_p, min_p, max_p) in lava_lab_prio.items():
            lab_config = runtimes[lab_name]
            assert lab_config.priority == fixed_p
            assert lab_config.priority_min == min_p
            assert lab_config.priority_max == max_p

    def test_runtimes(self):
        """Test all the runtime configs"""
        ref_data, config = self._load_config("tests/configs/runtimes.yaml")
        ref_configs = ref_data["runtimes"]
        runtimes = self._reload(ref_data, config, "runtimes")
        runtime_names = [
            "docker",
            "k8s-gke-eu-west4",
            "lab-baylibre",
            "lab-collabora-staging",
            "shell",
        ]
        assert all(name in ref_configs for name in runtime_names)
        assert all(name in runtimes for name in runtime_names)
        assert runtimes["docker"]["user"] == "root"


class TestStorageConfigs(ConfigTest):
    """Tests related to storage configs"""

    def test_storage_configs(self):
        """Test the storage configs"""
        ref_data, config = self._load_config(
            "tests/configs/storage-configs.yaml"
        )
        ref_configs = ref_data["storage"]
        storage_configs = self._reload(ref_data, config, "storage")
        config_names = ["local", "staging.kernelci.org", "staging-backend"]
        assert all(name in ref_configs for name in config_names)
        assert all(name in storage_configs for name in config_names)
        assert storage_configs["local"]["host"] == "172.17.0.1"


class TestSchedulerConfigs(ConfigTest):
    """Tests related to the scheduler configs"""

    def test_scheduler_conigs(self):
        """Test all the scheduler config entries"""
        ref_data, config = self._load_config("tests/configs/scheduler.yaml")
        scheduler_config = self._reload(ref_data, config, "scheduler")
        kunit_job = None
        for entry in scheduler_config:
            if entry["job"] == "kunit":
                kunit_job = entry
        assert kunit_job is not None
        assert kunit_job["runtime"]["name"] == "k8s-gke-eu-west4"
