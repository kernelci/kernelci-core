# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2025 Collabora Limited
# Author: Denys Fedoryshchenko <denys.f@collabora.com>

"""Unit tests for the kernelci.context module"""

import argparse
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import yaml
import toml

from kernelci.context import KContext, create_context, create_context_from_args


class TestKContext(unittest.TestCase):
    """Test cases for KContext class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()

        # Create sample YAML config
        self.yaml_config = {
            'api': {
                'production': {
                    'url': 'https://api.kernelci.org',
                    'version': 'v1',
                    'timeout': 60
                },
                'staging': {
                    'url': 'https://staging-api.kernelci.org',
                    'version': 'v1',
                    'timeout': 30
                }
            },
            'storage': {
                'main': {
                    'storage_type': 'backend',
                    'base_url': 'https://storage.kernelci.org',
                    'api_url': 'https://storage-api.kernelci.org'
                }
            },
            'jobs': {
                'test-job': {
                    'template': 'test.jinja2',
                    'kind': 'test'
                }
            }
        }

        # Create sample TOML secrets
        self.toml_secrets = {
            'api': {
                'production': {
                    'token': 'prod-token-123'
                },
                'staging': {
                    'token': 'staging-token-456'
                }
            },
            'storage': {
                'main': {
                    'storage_cred': 'storage-secret-789'
                }
            }
        }

        # Write test files
        self.yaml_path = os.path.join(self.test_dir, 'config.yaml')
        with open(self.yaml_path, 'w') as f:
            yaml.dump(self.yaml_config, f)

        self.toml_path = os.path.join(self.test_dir, 'secrets.toml')
        with open(self.toml_path, 'w') as f:
            toml.dump(self.toml_secrets, f)

    def tearDown(self):
        """Clean up test fixtures"""
        # Remove test files
        import shutil
        shutil.rmtree(self.test_dir)

    def test_init_with_paths(self):
        """Test KContext initialization with explicit paths"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        self.assertIsNotNone(ctx.config)
        self.assertIsNotNone(ctx.secrets)
        self.assertEqual(ctx.config_paths, [self.yaml_path])
        self.assertEqual(ctx.secrets_path, self.toml_path)

    def test_init_with_args(self):
        """Test KContext initialization with CLI arguments"""
        args = argparse.Namespace(
            config=self.yaml_path,
            secrets=self.toml_path,
            name='test-program'
        )

        ctx = KContext(args=args)

        self.assertEqual(ctx.program_name, 'test-program')
        self.assertIsNotNone(ctx.config)
        self.assertIsNotNone(ctx.secrets)

    def test_get_config(self):
        """Test getting configuration values"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        # Test nested access
        url = ctx.get_config('api.production.url')
        self.assertEqual(url, 'https://api.kernelci.org')

        # Test default value
        missing = ctx.get_config('api.nonexistent', default='default-value')
        self.assertEqual(missing, 'default-value')

    def test_get_secret(self):
        """Test getting secret values"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        # Test nested access
        token = ctx.get_secret('api.production.token')
        self.assertEqual(token, 'prod-token-123')

        # Test default value
        missing = ctx.get_secret('api.nonexistent.token', default='default-token')
        self.assertEqual(missing, 'default-token')

    def test_get_api_config(self):
        """Test getting API configuration with secrets"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        api_config = ctx.get_api_config('production')

        self.assertIsNotNone(api_config)
        self.assertEqual(api_config['url'], 'https://api.kernelci.org')
        self.assertEqual(api_config['token'], 'prod-token-123')
        self.assertEqual(api_config['version'], 'v1')
        self.assertEqual(api_config['timeout'], 60)

    def test_get_storage_config(self):
        """Test getting storage configuration with credentials"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        storage_config = ctx.get_storage_config('main')

        self.assertIsNotNone(storage_config)
        self.assertEqual(storage_config['storage_type'], 'backend')
        self.assertEqual(storage_config['base_url'], 'https://storage.kernelci.org')
        self.assertEqual(storage_config['storage_cred'], 'storage-secret-789')

    def test_get_job_config(self):
        """Test getting job configuration"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        job_config = ctx.get_job_config('test-job')

        self.assertIsNotNone(job_config)
        self.assertEqual(job_config['template'], 'test.jinja2')
        self.assertEqual(job_config['kind'], 'test')

    def test_get_all_configs(self):
        """Test getting all configurations"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        all_configs = ctx.get_all_configs()

        self.assertIsNotNone(all_configs)
        self.assertIn('api', all_configs)
        self.assertIn('storage', all_configs)
        self.assertIn('jobs', all_configs)

    def test_get_all_secrets(self):
        """Test getting all secrets"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        all_secrets = ctx.get_all_secrets()

        self.assertIsNotNone(all_secrets)
        self.assertIn('api', all_secrets)
        self.assertIn('storage', all_secrets)

    def test_get_section_configs(self):
        """Test getting all configurations for a section"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        api_configs = ctx.get_section_configs('api')

        self.assertIsNotNone(api_configs)
        self.assertIn('production', api_configs)
        self.assertIn('staging', api_configs)

    def test_merge_config_and_secrets(self):
        """Test merging configuration and secrets"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        merged = ctx.merge_config_and_secrets('api.production', 'api.production')

        self.assertIsNotNone(merged)
        self.assertEqual(merged['url'], 'https://api.kernelci.org')
        self.assertEqual(merged['token'], 'prod-token-123')

    def test_missing_files(self):
        """Test handling of missing configuration files"""
        ctx = KContext(
            config_paths='nonexistent.yaml',
            secrets_path='nonexistent.toml'
        )

        self.assertEqual(ctx.config, {})
        self.assertEqual(ctx.secrets, {})

    def test_directory_loading(self):
        """Test loading YAML files from a directory"""
        # Create a subdirectory with multiple YAML files
        config_dir = os.path.join(self.test_dir, 'configs')
        os.makedirs(config_dir)

        # Write multiple YAML files
        api_config = {'api': {'test': {'url': 'https://test.com'}}}
        storage_config = {'storage': {'test': {'base_url': 'https://storage.test.com'}}}

        with open(os.path.join(config_dir, 'api.yaml'), 'w') as f:
            yaml.dump(api_config, f)

        with open(os.path.join(config_dir, 'storage.yaml'), 'w') as f:
            yaml.dump(storage_config, f)

        ctx = KContext(config_paths=config_dir)

        # Check that both files were loaded and merged
        self.assertEqual(ctx.get_config('api.test.url'), 'https://test.com')
        self.assertEqual(ctx.get_config('storage.test.base_url'), 'https://storage.test.com')

    def test_factory_functions(self):
        """Test factory functions for creating KContext"""
        # Test create_context
        ctx1 = create_context(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path,
            program_name='test'
        )
        self.assertIsInstance(ctx1, KContext)
        self.assertEqual(ctx1.program_name, 'test')

        # Test create_context_from_args
        args = argparse.Namespace(
            config=self.yaml_path,
            secrets=self.toml_path,
            name='test-from-args'
        )
        ctx2 = create_context_from_args(args)
        self.assertIsInstance(ctx2, KContext)
        self.assertEqual(ctx2.program_name, 'test-from-args')

    def test_repr(self):
        """Test string representation of KContext"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path,
            program_name='test'
        )

        repr_str = repr(ctx)
        self.assertIn(self.yaml_path, repr_str)
        self.assertIn(self.toml_path, repr_str)
        self.assertIn('test', repr_str)

    def test_alternative_secret_formats(self):
        """Test alternative secret location formats"""
        # Create secrets with alternative format
        alt_secrets = {
            'kci': {
                'secrets': {
                    'api': {
                        'alt-api': {
                            'token': 'alt-token'
                        }
                    },
                    'storage': {
                        'alt-storage': {
                            'password': 'alt-password'
                        }
                    }
                }
            }
        }

        alt_toml_path = os.path.join(self.test_dir, 'alt_secrets.toml')
        with open(alt_toml_path, 'w') as f:
            toml.dump(alt_secrets, f)

        # Create config for alternative APIs
        alt_config = {
            'api': {
                'alt-api': {'url': 'https://alt-api.com'}
            },
            'storage': {
                'alt-storage': {'base_url': 'https://alt-storage.com'}
            }
        }

        alt_yaml_path = os.path.join(self.test_dir, 'alt_config.yaml')
        with open(alt_yaml_path, 'w') as f:
            yaml.dump(alt_config, f)

        ctx = KContext(
            config_paths=alt_yaml_path,
            secrets_path=alt_toml_path
        )

        # Test API with alternative secret location
        api_config = ctx.get_api_config('alt-api')
        self.assertEqual(api_config['token'], 'alt-token')

        # Test storage with password instead of storage_cred
        storage_config = ctx.get_storage_config('alt-storage')
        self.assertEqual(storage_config['storage_cred'], 'alt-password')

    def test_parse_cli_args(self):
        """Test parsing CLI arguments directly"""
        # Mock sys.argv
        test_args = [
            'test_program',
            '--settings', self.toml_path,
            '--name', 'scheduler_k8s',
            '--runtimes', 'k8s-gke-eu-west4', 'k8s-all',
            'loop'  # Extra arg that should be ignored
        ]

        with patch.object(sys, 'argv', test_args):
            ctx = KContext(parse_cli=True)

            # Check parsed values
            self.assertEqual(ctx.program_name, 'scheduler_k8s')
            self.assertEqual(ctx.secrets_path, self.toml_path)
            self.assertListEqual(ctx.get_runtimes(), ['k8s-gke-eu-west4', 'k8s-all'])
            self.assertIsNotNone(ctx.get_cli_args())

            # Check that secrets were loaded
            token = ctx.get_secret('api.production.token')
            self.assertEqual(token, 'prod-token-123')

    def test_parse_cli_with_config(self):
        """Test parsing CLI arguments with config path"""
        test_args = [
            'test_program',
            '--config', self.yaml_path,
            '--settings', self.toml_path,
            '--name', 'test_service'
        ]

        with patch.object(sys, 'argv', test_args):
            ctx = KContext(parse_cli=True)

            # Check config was loaded
            api_url = ctx.get_config('api.production.url')
            self.assertEqual(api_url, 'https://api.kernelci.org')

            # Check name was set
            self.assertEqual(ctx.program_name, 'test_service')

    def test_get_runtimes(self):
        """Test getting runtimes from CLI arguments"""
        args = argparse.Namespace(
            config=self.yaml_path,
            settings=self.toml_path,
            runtimes=['runtime1', 'runtime2', 'runtime3'],
            name='test'
        )

        ctx = KContext(args=args)

        runtimes = ctx.get_runtimes()
        self.assertListEqual(runtimes, ['runtime1', 'runtime2', 'runtime3'])

    def test_settings_alias(self):
        """Test that --settings works as alias for secrets"""
        args = argparse.Namespace(
            config=self.yaml_path,
            settings=self.toml_path,  # Using settings instead of secrets
            name='test',
            runtimes=[]
        )

        ctx = KContext(args=args)

        # Should still load secrets from settings path
        token = ctx.get_secret('api.production.token')
        self.assertEqual(token, 'prod-token-123')

    def test_empty_runtimes(self):
        """Test handling of empty runtimes list"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        runtimes = ctx.get_runtimes()
        self.assertListEqual(runtimes, [])

    def test_cli_args_without_parse_cli(self):
        """Test that cli_args is None when parse_cli is not used"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        self.assertIsNone(ctx.get_cli_args())

    def test_init_storage(self):
        """Test storage initialization"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        # Mock the storage module
        with patch('kernelci.storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_get_storage.return_value = mock_storage

            # Initialize storage
            storage = ctx.init_storage('main')

            # Check that storage was initialized
            self.assertEqual(storage, mock_storage)
            mock_get_storage.assert_called_once()

    def test_init_storage_missing_config(self):
        """Test storage initialization with missing configuration"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        # Try to initialize non-existent storage
        storage = ctx.init_storage('nonexistent')

        self.assertIsNone(storage)

    def test_init_api(self):
        """Test API initialization"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        # Initialize API
        api = ctx.init_api('production')

        self.assertIsNotNone(api)
        self.assertEqual(api['url'], 'https://api.kernelci.org')
        self.assertEqual(api['token'], 'prod-token-123')

    def test_get_storage_names(self):
        """Test getting list of storage names"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        storage_names = ctx.get_storage_names()

        self.assertIsInstance(storage_names, list)
        self.assertIn('main', storage_names)

    def test_get_api_names(self):
        """Test getting list of API names"""
        ctx = KContext(
            config_paths=self.yaml_path,
            secrets_path=self.toml_path
        )

        api_names = ctx.get_api_names()

        self.assertIsInstance(api_names, list)
        self.assertIn('production', api_names)
        self.assertIn('staging', api_names)


if __name__ == '__main__':
    unittest.main()
