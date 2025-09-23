#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2025 Collabora Limited
# Author: Denys Fedoryshchenko <denys.f@collabora.com>

"""Example usage of KernelCI Context module with CLI parsing"""

from kernelci.context import KContext


def main():
    # Example 1: Direct CLI parsing
    # Run this script with:
    # python example_context_usage.py --settings kernelci.toml --name scheduler_k8s --runtimes k8s-gke-eu-west4 k8s-all loop

    print("=== Example: Direct CLI Parsing ===")
    context = KContext(parse_cli=True)

    print(f"Program name: {context.program_name}")
    print(f"Runtimes: {context.get_runtimes()}")
    print(f"Settings path: {context.secrets_path}")
    print(f"Config paths: {context.config_paths}")

    # Access configuration and secrets
    if context.program_name:
        print(f"\nProcessing as {context.program_name}")

        # Get API configuration if available
        api_config = context.get_api_config("production")
        if api_config:
            print(f"API URL: {api_config.get('url', 'Not configured')}")
            if "token" in api_config:
                print("API token found (hidden)")

        # Process runtimes
        for runtime in context.get_runtimes():
            print(f"\nProcessing runtime: {runtime}")
            runtime_config = context.get_runtime_config(runtime)
            if runtime_config:
                print(f"  Runtime config: {runtime_config}")
            else:
                print(f"  No configuration found for runtime: {runtime}")

    # Example: Initialize storage
    print("\n=== Storage Initialization Example ===")
    storage_names = context.get_storage_names()
    print(f"Available storage configs: {storage_names}")

    if storage_names:
        storage_name = storage_names[0]  # Use first available storage
        print(f"\nInitializing storage: {storage_name}")
        storage = context.init_storage(storage_name)
        if storage:
            print(f"  Storage '{storage_name}' initialized successfully")
            print(f"  Storage type: {storage.config.storage_type}")
            print(f"  Base URL: {storage.config.base_url}")
        else:
            print(f"  Failed to initialize storage '{storage_name}'")

    # Example: Initialize API
    print("\n=== API Initialization Example ===")
    api_names = context.get_api_names()
    print(f"Available API configs: {api_names}")

    if api_names:
        api_name = api_names[0]  # Use first available API
        print(f"\nInitializing API: {api_name}")
        api = context.init_api(api_name)
        if api:
            print(f"  API '{api_name}' initialized successfully")
            print(f"  URL: {api.get('url', 'Not configured')}")
            if "token" in api:
                print("  Token: [HIDDEN]")
        else:
            print(f"✗ Failed to initialize API '{api_name}'")

    print("\n=== Example completed successfully ===")


if __name__ == "__main__":
    main()
