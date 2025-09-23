# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2025 Collabora Limited
# Author: Denys Fedoryshchenko <denys.f@collabora.com>

"""KernelCI Context Module - Unified interface for config and secrets management

This module provides a unified interface for managing configuration and secrets
in KernelCI applications. It handles loading YAML configuration files and TOML
secrets files, and provides methods to access them in a structured way.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import toml
import yaml

import kernelci.config
import kernelci.storage


class KContext:
    """KernelCI Context class for managing configuration and secrets

    This class provides a unified interface for accessing configuration
    loaded from YAML files and secrets loaded from TOML files. It handles
    the merging of multiple configuration sources and provides convenient
    methods for accessing specific configuration sections like API and storage.

    Attributes:
        config: Dictionary containing loaded configuration from YAML files
        secrets: Dictionary containing loaded secrets from TOML files
        program_name: Name of the program/section to identify in configs
        config_paths: List of paths to configuration files/directories
        secrets_path: Path to the secrets TOML file
        runtimes: List of runtimes from CLI arguments
        cli_args: Parsed CLI arguments if parse_cli=True was used
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        args: Optional[argparse.Namespace] = None,
        config_paths: Optional[Union[str, List[str]]] = None,
        secrets_path: Optional[str] = None,
        program_name: Optional[str] = None,
        parse_cli: bool = False,
    ):
        """Initialize KContext with configuration and secrets

        Args:
            args: CLI arguments namespace (if provided, overrides other params)
            config_paths: Path(s) to YAML config file(s) or directory(ies)
            secrets_path: Path to TOML secrets file
            program_name: Name of the program/section for identification
            parse_cli: If True, parse CLI arguments directly from sys.argv
        """
        # Parse CLI arguments if requested
        if parse_cli:
            args = self._parse_cli_args()

        # Initialize runtime list
        self.runtimes = []
        self.cli_args = args if parse_cli else None

        # Extract values from CLI arguments if provided
        if args:
            config_paths = getattr(args, "config", None) or config_paths
            # Handle --settings parameter (alias for secrets)
            secrets_path = (
                getattr(args, "settings", None)
                or getattr(args, "secrets", None)
                or secrets_path
            )
            program_name = getattr(args, "name", None) or program_name
            # Handle --runtimes parameter
            self.runtimes = getattr(args, "runtimes", [])

        # Set default paths if not provided
        if not config_paths:
            # Check default locations
            default_locations = ["config/core", "/etc/kernelci/core"]
            for loc in default_locations:
                if os.path.exists(loc):
                    config_paths = loc
                    break

        if not secrets_path:
            # Check default secrets locations
            default_secrets = ["kernelci.toml", "/etc/kernelci/secrets.toml"]
            for loc in default_secrets:
                if os.path.exists(loc):
                    secrets_path = loc
                    break

        # Store attributes
        self.config_paths = (
            config_paths
            if isinstance(config_paths, list)
            else [config_paths] if config_paths else []
        )
        self.secrets_path = secrets_path
        self.program_name = program_name

        # Load configuration and secrets
        self.config = self._load_config()
        self.secrets = self._load_secrets()

    def _parse_cli_args(self) -> argparse.Namespace:
        """Parse command line arguments directly from sys.argv

        Returns:
            Namespace with parsed CLI arguments
        """
        # First, find where --runtimes appears and extract its values
        argv = sys.argv[1:]  # Skip program name
        runtimes = []

        # Find --runtimes and collect its values
        i = 0
        while i < len(argv):
            if argv[i] == "--runtimes":
                i += 1
                # Collect values until we hit another option or end
                while i < len(argv):
                    # Stop at next option (starts with --) or certain known commands
                    if argv[i].startswith("--"):
                        break
                    # Also check if this looks like a command rather than a runtime
                    # Common commands: loop, run, start, stop, etc.
                    # For now, we'll just check if it contains common runtime patterns
                    if "." in argv[i] or "-" in argv[i] or argv[i].startswith("k8s"):
                        runtimes.append(argv[i])
                        i += 1
                    else:
                        # This looks like a command, stop here
                        break
                break
            i += 1

        # Now parse the standard arguments
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--settings", help="Path to TOML settings/secrets file")
        parser.add_argument(
            "--secrets", help="Path to TOML secrets file (alias for settings)"
        )
        parser.add_argument("--config", help="Path to YAML config file or directory")
        parser.add_argument("--name", help="Program/section name")

        # Parse known args only to avoid conflicts with main program arguments
        args, _ = parser.parse_known_args()

        # Add the runtimes we extracted
        args.runtimes = runtimes

        return args

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML files

        Returns:
            Dictionary containing merged configuration from all YAML files
        """
        if not self.config_paths:
            return {}

        config = {}

        for path in self.config_paths:
            if not path or not os.path.exists(path):
                continue

            if os.path.isfile(path) and path.endswith(".yaml"):
                # Load single YAML file
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    config = kernelci.config.merge_trees(config, data)
            elif os.path.isdir(path):
                # Load all YAML files from directory using kernelci.config
                data = kernelci.config.load_yaml(path)
                config = kernelci.config.merge_trees(config, data)

        return config

    def _load_secrets(self) -> Dict[str, Any]:
        """Load secrets from TOML file

        Returns:
            Dictionary containing secrets from TOML file
        """
        if not self.secrets_path or not os.path.exists(self.secrets_path):
            return {}

        try:
            with open(self.secrets_path, "r", encoding="utf-8") as f:
                return toml.load(f)
        except (OSError, IOError, toml.TomlDecodeError) as e:
            print(
                f"Warning: Failed to load secrets from {self.secrets_path}: {e}",
                file=sys.stderr,
            )
            return {}

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key path

        Args:
            key: Dot-separated key path (e.g., 'api.production.url')
            default: Default value if key not found

        Returns:
            Configuration value or default if not found
        """
        return self._get_nested_value(self.config, key, default)

    def get_secret(self, key: str, default: Any = None) -> Any:
        """Get secret value by key path

        Args:
            key: Dot-separated key path (e.g., 'api.production.token')
            default: Default value if key not found

        Returns:
            Secret value or default if not found
        """
        return self._get_nested_value(self.secrets, key, default)

    def _get_nested_value(
        self, data: Dict[str, Any], key: str, default: Any = None
    ) -> Any:
        """Get nested value from dictionary using dot notation

        Args:
            data: Dictionary to search
            key: Dot-separated key path
            default: Default value if key not found

        Returns:
            Value at key path or default if not found
        """
        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    def get_api_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get API configuration with URL and token

        Args:
            name: Name of the API configuration

        Returns:
            Dictionary with API configuration including URL and token, or None
        """
        # Get API config from YAML
        api_config = self.get_config(f"api.{name}")
        if not api_config:
            return None

        # Create result dictionary
        result = {}
        if isinstance(api_config, dict):
            result = api_config.copy()
        else:
            result["url"] = api_config

        # Add token from secrets if available
        token = self.get_secret(f"api.{name}.token")
        if token:
            result["token"] = token

        # Also check for alternative secret locations
        if not token:
            # Check kci.secrets.api.name.token format
            token = self.get_secret(f"kci.secrets.api.{name}.token")
            if token:
                result["token"] = token

        return result

    def get_storage_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get storage configuration with credentials

        Args:
            name: Name of the storage configuration

        Returns:
            Dictionary with storage configuration including credentials, or None
        """
        # Get storage config from YAML
        storage_config = self.get_config(f"storage.{name}")
        if not storage_config:
            return None

        # Create result dictionary
        result = {}
        if isinstance(storage_config, dict):
            result = storage_config.copy()
        else:
            result["base_url"] = storage_config

        # Add credentials from secrets if available
        cred = self.get_secret(f"storage.{name}.storage_cred")
        if cred:
            result["storage_cred"] = cred

        # Also check for alternative secret locations
        if not cred:
            # Check for password format
            cred = self.get_secret(f"storage.{name}.password")
            if cred:
                result["storage_cred"] = cred
            # Check kci.secrets format
            cred = self.get_secret(f"kci.secrets.storage.{name}.password")
            if cred:
                result["storage_cred"] = cred

        return result

    def get_runtime_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get runtime configuration

        Args:
            name: Name of the runtime configuration

        Returns:
            Dictionary with runtime configuration, or None
        """
        return self.get_config(f"runtimes.{name}")

    def get_platform_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get platform configuration

        Args:
            name: Name of the platform configuration

        Returns:
            Dictionary with platform configuration, or None
        """
        return self.get_config(f"platforms.{name}")

    def get_job_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get job configuration

        Args:
            name: Name of the job configuration

        Returns:
            Dictionary with job configuration, or None
        """
        return self.get_config(f"jobs.{name}")

    def get_scheduler_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get scheduler configuration

        Args:
            name: Name of the scheduler configuration

        Returns:
            Dictionary with scheduler configuration, or None
        """
        return self.get_config(f"scheduler.{name}")

    def get_tree_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tree configuration

        Args:
            name: Name of the tree configuration

        Returns:
            Dictionary with tree configuration, or None
        """
        return self.get_config(f"trees.{name}")

    def get_build_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get build configuration

        Args:
            name: Name of the build configuration

        Returns:
            Dictionary with build configuration, or None
        """
        return self.get_config(f"build_configs.{name}")

    def get_runtimes(self) -> List[str]:
        """Get list of runtimes from CLI arguments

        Returns:
            List of runtime names
        """
        return self.runtimes

    def get_cli_args(self) -> Optional[argparse.Namespace]:
        """Get parsed CLI arguments if parse_cli was used

        Returns:
            Namespace with CLI arguments or None
        """
        return self.cli_args

    def init_storage(self, name: str) -> Optional["kernelci.storage.Storage"]:
        """Initialize a storage instance with configuration and credentials

        This method loads the storage configuration and credentials, creates
        the appropriate configuration object, and returns an initialized
        storage instance ready for use.

        Args:
            name: Name of the storage configuration

        Returns:
            Initialized Storage instance or None if configuration not found

        Example:
            storage = ctx.init_storage('main-storage')
            if storage:
                url = storage.upload_single(('file.txt', 'remote.txt'))
        """
        # Get storage configuration
        storage_config_data = self.get_storage_config(name)
        if not storage_config_data:
            return None

        # Load the full configuration objects using kernelci.config
        config_data = {"storage": {name: storage_config_data}}
        loaded_configs = kernelci.config.load_data(config_data)

        # Get the storage config object
        storage_configs = loaded_configs.get("storage", {})
        storage_config = storage_configs.get(name)

        if not storage_config:
            return None

        # Get credentials
        credentials = storage_config_data.get("storage_cred")

        # Initialize storage
        try:
            return kernelci.storage.get_storage(storage_config, credentials)
        except (AttributeError, ValueError, TypeError) as e:
            print(f"Failed to initialize storage '{name}': {e}", file=sys.stderr)
            return None

    def init_api(self, name: str) -> Optional[Dict[str, Any]]:
        """Initialize API client configuration with URL and token

        Args:
            name: Name of the API configuration

        Returns:
            Dictionary with API configuration including URL and token, or None

        Example:
            api = ctx.init_api('production')
            if api:
                # Use api['url'] and api['token'] for requests
                headers = {'Authorization': f"Bearer {api['token']}"}
        """
        return self.get_api_config(name)

    def get_storage_names(self) -> List[str]:
        """Get list of all available storage configuration names

        Returns:
            List of storage configuration names
        """
        storage_section = self._get_section_configs("storage")
        if storage_section and isinstance(storage_section, dict):
            return list(storage_section.keys())
        return []

    def get_api_names(self) -> List[str]:
        """Get list of all available API configuration names

        Returns:
            List of API configuration names
        """
        api_section = self._get_section_configs("api")
        if api_section and isinstance(api_section, dict):
            return list(api_section.keys())
        return []

    def get_all_configs(self) -> Dict[str, Any]:
        """Get all loaded configuration

        Returns:
            Dictionary containing all loaded configuration
        """
        return self.config.copy()

    def get_all_secrets(self) -> Dict[str, Any]:
        """Get all loaded secrets

        Returns:
            Dictionary containing all loaded secrets
        """
        return self.secrets.copy()

    def get_section_configs(self, section: str) -> Optional[Dict[str, Any]]:
        """Get all configurations for a specific section

        Args:
            section: Name of the configuration section (e.g., 'api', 'storage')

        Returns:
            Dictionary with all configurations for the section, or None
        """
        return self.get_config(section)

    def get_section_secrets(self, section: str) -> Optional[Dict[str, Any]]:
        """Get all secrets for a specific section

        Args:
            section: Name of the secrets section

        Returns:
            Dictionary with all secrets for the section, or None
        """
        return self.get_secret(section)

    def merge_config_and_secrets(
        self, config_key: str, secret_key: str
    ) -> Dict[str, Any]:
        """Merge configuration and secrets for a specific key

        Args:
            config_key: Key path for configuration
            secret_key: Key path for secrets

        Returns:
            Merged dictionary with both config and secrets
        """
        config = self.get_config(config_key) or {}
        secrets = self.get_secret(secret_key) or {}

        if isinstance(config, dict):
            result = config.copy()
            if isinstance(secrets, dict):
                result.update(secrets)
            return result

        return {"value": config, "secrets": secrets}

    def __repr__(self) -> str:
        """String representation of KContext

        Returns:
            String representation showing config and secrets paths
        """
        return (
            f"KContext(config_paths={self.config_paths}, "
            f"secrets_path={self.secrets_path}, "
            f"program_name={self.program_name})"
        )


def create_context(
    config_paths: Optional[Union[str, List[str]]] = None,
    secrets_path: Optional[str] = None,
    program_name: Optional[str] = None,
) -> KContext:
    """Factory function to create a KContext instance

    Args:
        config_paths: Path(s) to YAML config file(s) or directory(ies)
        secrets_path: Path to TOML secrets file
        program_name: Name of the program/section for identification

    Returns:
        KContext instance with loaded configuration and secrets
    """
    return KContext(
        config_paths=config_paths, secrets_path=secrets_path, program_name=program_name
    )


def create_context_from_args(args: argparse.Namespace) -> KContext:
    """Create KContext from command line arguments

    Args:
        args: Parsed command line arguments

    Returns:
        KContext instance initialized from CLI arguments
    """
    return KContext(args=args)
