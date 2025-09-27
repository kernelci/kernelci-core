# KernelCI Context Module

## Overview

The KernelCI Context module provides a unified interface for managing configuration and secrets in KernelCI applications. It simplifies the process of loading YAML configuration files and TOML secrets files, and provides convenient methods to access them in a structured way.

## Installation

The module is part of the kernelci-core package. No additional installation is required.

## Usage

### Basic Usage

```python
from kernelci.context import KContext

# Create context with default paths
ctx = KContext()

# Access configuration values
api_url = ctx.get_config('api.production.url')
api_token = ctx.get_secret('api.production.token')
```

### Direct CLI Parsing

```python
from kernelci.context import KContext

# In your main script, parse CLI arguments directly
if __name__ == '__main__':
    # This will automatically parse --settings, --runtimes, --name from sys.argv
    context = KContext(parse_cli=True)

    # Access parsed values
    program_name = context.program_name
    runtimes = context.get_runtimes()  # Returns list of runtimes

    # Access configuration and secrets
    api_config = context.get_api_config('production')
```

### With Custom Paths

```python
from kernelci.context import KContext

# Create context with custom paths
ctx = KContext(
    config_paths=['config/core', '/etc/kernelci/core'],
    secrets_path='kernelci.toml',
    program_name='my_program'
)

# Access configuration
storage_config = ctx.get_storage_config('main-storage')
```

### CLI Integration

```python
import argparse
from kernelci.context import create_context_from_args

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--config', help='Path to config file or directory')
parser.add_argument('--settings', help='Path to settings/secrets TOML file')
parser.add_argument('--name', help='Program name')
parser.add_argument('--runtimes', nargs='*', help='List of runtimes')
args = parser.parse_args()

# Create context from CLI arguments
ctx = create_context_from_args(args)

# Access runtimes
runtimes = ctx.get_runtimes()
```

## Configuration Structure

### YAML Configuration Files

Configuration files should be in YAML format. Multiple files can be loaded and merged:

```yaml
# api.yaml
api:
  production:
    url: "https://api.kernelci.org"
    version: "v1"
    timeout: 60

  staging:
    url: "https://staging-api.kernelci.org"
    version: "v1"
    timeout: 30

# storage.yaml
storage:
  main-storage:
    storage_type: backend
    base_url: "https://storage.kernelci.org"
    api_url: "https://storage-api.kernelci.org"
```

### TOML Secrets File

Secrets are stored in TOML format:

```toml
# kernelci.toml
[api.production]
token = "production-api-token-here"

[api.staging]
token = "staging-api-token-here"

[storage.main-storage]
storage_cred = "storage-credential-here"
```

## API Reference

### KContext Class

#### `__init__(args=None, config_paths=None, secrets_path=None, program_name=None, parse_cli=False)`

Initialize the context with configuration and secrets.

- **args**: CLI arguments namespace (overrides other parameters if provided)
- **config_paths**: Path(s) to YAML config file(s) or directory(ies)
- **secrets_path**: Path to TOML secrets file
- **program_name**: Name of the program/section for identification
- **parse_cli**: If True, automatically parse CLI arguments from sys.argv

When `parse_cli=True`, the following CLI arguments are automatically parsed:
- `--settings`: Path to TOML settings/secrets file
- `--secrets`: Alias for --settings
- `--config`: Path to YAML config file or directory
- `--name`: Program/section name
- `--runtimes`: List of runtime names (space-separated)

#### Configuration Access Methods

##### `get_config(key, default=None)`
Get configuration value by dot-separated key path.

```python
url = ctx.get_config('api.production.url')
timeout = ctx.get_config('api.production.timeout', default=60)
```

##### `get_secret(key, default=None)`
Get secret value by dot-separated key path.

```python
token = ctx.get_secret('api.production.token')
```

#### Section-Specific Methods

##### `get_api_config(name)`
Get API configuration with URL and token combined.

```python
api = ctx.get_api_config('production')
# Returns: {'url': '...', 'token': '...', ...}
```

##### `get_storage_config(name)`
Get storage configuration with credentials.

```python
storage = ctx.get_storage_config('main-storage')
# Returns: {'storage_type': '...', 'base_url': '...', 'storage_cred': '...'}
```

##### Other Section Methods
- `get_runtime_config(name)`: Get runtime configuration
- `get_platform_config(name)`: Get platform configuration
- `get_job_config(name)`: Get job configuration
- `get_scheduler_config(name)`: Get scheduler configuration
- `get_tree_config(name)`: Get tree configuration
- `get_build_config(name)`: Get build configuration
- `get_runtimes()`: Get list of runtime names from CLI arguments
- `get_cli_args()`: Get parsed CLI arguments (if parse_cli=True was used)

#### Service Initialization Methods

##### `init_storage(name)`
Initialize a storage instance with configuration and credentials. Returns a ready-to-use Storage object.

```python
storage = ctx.init_storage('main-storage')
if storage:
    url = storage.upload_single(('local.txt', 'remote.txt'))
```

##### `init_api(name)`
Initialize API client configuration with URL and token. Returns a dictionary with API details.

```python
api = ctx.init_api('production')
if api:
    headers = {'Authorization': f"Bearer {api['token']}"}
    response = requests.get(f"{api['url']}/nodes", headers=headers)
```

##### `get_storage_names()`
Get list of all available storage configuration names.

##### `get_api_names()`
Get list of all available API configuration names.

#### Utility Methods

##### `get_all_configs()`
Get all loaded configuration as a dictionary.

##### `get_all_secrets()`
Get all loaded secrets as a dictionary.

##### `get_section_configs(section)`
Get all configurations for a specific section.

```python
all_apis = ctx.get_section_configs('api')
```

##### `merge_config_and_secrets(config_key, secret_key)`
Merge configuration and secrets for specific keys.

### Factory Functions

#### `create_context(config_paths=None, secrets_path=None, program_name=None)`
Create a KContext instance with the specified parameters.

#### `create_context_from_args(args)`
Create a KContext instance from parsed command-line arguments.

## Examples

### Complete Example: API Client Setup

```python
from kernelci.context import KContext
import requests

# Create context
ctx = KContext(
    config_paths='config/core',
    secrets_path='kernelci.toml'
)

# Get API configuration
api_config = ctx.get_api_config('production')

if api_config:
    # Make API request
    headers = {'Authorization': f"Bearer {api_config['token']}"}
    response = requests.get(
        f"{api_config['url']}/nodes",
        headers=headers,
        timeout=api_config.get('timeout', 60)
    )
```

### Storage Upload Example

```python
from kernelci.context import KContext

# Create context
ctx = KContext()

# Method 1: Using init_storage (recommended)
storage = ctx.init_storage('main-storage')
if storage:
    # Upload file directly
    url = storage.upload_single(
        ('local_file.txt', 'remote_file.txt'),
        dest_path='results/'
    )
    print(f"File uploaded to: {url}")

# Method 2: Manual initialization (for advanced use cases)
from kernelci.storage import get_storage

storage_config = ctx.get_storage_config('main-storage')
if storage_config:
    # Create storage instance manually
    storage = get_storage(
        config=storage_config,
        credentials=storage_config.get('storage_cred')
    )
    # Use storage...
```

### Service Initialization Example

```python
from kernelci.context import KContext

# Initialize context
ctx = KContext(
    config_paths='config/core',
    secrets_path='kernelci.toml'
)

# Initialize storage service
storage = ctx.init_storage('main-storage')
if storage:
    # Storage is ready to use
    print("Storage initialized successfully")
    url = storage.upload_single(('test.log', 'logs/test.log'))

# Initialize API configuration
api = ctx.init_api('production')
if api:
    # API config with URL and token
    print(f"API URL: {api['url']}")
    # Use api['token'] for authentication

# List available configurations
print(f"Available storage configs: {ctx.get_storage_names()}")
print(f"Available API configs: {ctx.get_api_names()}")
```

### Docker Compose Example

```python
from kernelci.context import KContext

# Example from docker-compose.yml:
# command: ['--settings=/home/kernelci/config/kernelci.toml', 'loop', '--name=scheduler_k8s', '--runtimes', 'k8s-gke-eu-west4', 'k8s-all']

if __name__ == '__main__':
    # Automatically parse CLI arguments
    context = KContext(parse_cli=True)

    # Access parsed values
    print(f"Program: {context.program_name}")  # scheduler_k8s
    print(f"Runtimes: {context.get_runtimes()}")  # ['k8s-gke-eu-west4', 'k8s-all']

    # Initialize storage for the scheduler
    storage = context.init_storage('results-storage')
    if not storage:
        print("Warning: Storage not configured")

    # The settings file is automatically loaded
    api_config = context.get_api_config('production')

    # Start your application logic
    if context.program_name == 'scheduler_k8s':
        for runtime in context.get_runtimes():
            runtime_config = context.get_runtime_config(runtime)
            # Process each runtime...
```

## Best Practices

1. **Use Default Paths**: When possible, rely on default paths for configuration and secrets
2. **Environment-Specific Secrets**: Keep separate TOML files for different environments
3. **Validate Configuration**: Always check if configuration exists before using it
4. **Handle Missing Secrets**: Provide appropriate error handling for missing credentials
5. **Merge Multiple Sources**: Use the directory loading feature to split configuration across multiple files

## Error Handling

The module provides graceful error handling:

- Missing configuration files return empty dictionaries
- Invalid YAML/TOML files print warnings but don't crash
- Missing keys return `None` or the specified default value
- Path resolution checks multiple default locations

## Security Considerations

- Store secrets files with appropriate file permissions (e.g., 600)
- Never commit secrets files to version control
- Use environment variables for sensitive data in CI/CD pipelines
- Consider using secret management services for production deployments