# LastCron

[![PyPI version](https://badge.fury.io/py/lastcron.svg)](https://badge.fury.io/py/lastcron)
[![Python Versions](https://img.shields.io/pypi/pyversions/lastcron.svg)](https://pypi.org/project/lastcron/)
[![License](https://img.shields.io/badge/License-Elastic%202.0-blue.svg)](LICENSE)
[![CI](https://github.com/allanbru/lastcron-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/allanbru/lastcron-sdk/actions/workflows/ci.yml)

**LastCron** is a Python SDK for building and orchestrating workflows with the LastCron platform. It provides a simple, decorator-based API for creating flows that can be scheduled, monitored, and managed through a centralized orchestration system.

## ✨ Features

- **🎯 Simple Decorator API**: Mark functions as flows with a single `@flow` decorator
- **🔄 Flow Orchestration**: Trigger and chain flows programmatically
- **📊 Automatic Logging**: Built-in logger that sends logs to the orchestrator
- **🔐 Secret Management**: Secure handling of secrets with automatic redaction
- **⏰ Scheduling**: Schedule flows for immediate or future execution
- **🔍 Type Safety**: Strongly-typed dataclasses for all API responses
- **⚡ Async Support**: Both synchronous and asynchronous API clients
- **📦 On-Demand Configuration**: Fetch configuration blocks only when needed

## 📦 Installation

Install LastCron using pip:

```bash
pip install lastcron
```

Or with optional development dependencies:

```bash
pip install lastcron[dev]
```

## 🚀 Quick Start

### Basic Flow

Create a simple flow that logs messages:

```python
from lastcron import flow, get_run_logger, get_workspace_id

@flow
def hello_world(**params):
    logger = get_run_logger()
    workspace_id = get_workspace_id()
    
    logger.info(f"Hello from workspace {workspace_id}!")
    logger.info(f"Parameters: {params}")
```

### Triggering Other Flows

Chain flows together by triggering them programmatically:

```python
from lastcron import flow, get_run_logger

@flow
def data_processing(**params):
    logger = get_run_logger()
    logger.info("Processing data...")
    # Your data processing logic here

@flow
def orchestrator(**params):
    logger = get_run_logger()
    
    # Trigger another flow using .submit()
    run = data_processing.submit(
        parameters={'batch_size': 100}
    )
    
    if run:
        logger.info(f"Triggered run ID: {run.id}")
```

### Using Configuration Blocks

Retrieve configuration and secrets on-demand:

```python
from lastcron import flow, get_block, get_run_logger

@flow
def api_integration(**params):
    logger = get_run_logger()
    
    # Get API credentials (automatically decrypted if secret)
    api_key = get_block('api-key')
    
    if api_key:
        logger.info("Retrieved API credentials")
        # The secret value is automatically redacted from logs
        # Use api_key.value for the actual key
```

### Scheduling Flows

Schedule flows for future execution:

```python
from lastcron import flow, run_flow, get_run_logger
from datetime import datetime, timedelta

@flow
def scheduler(**params):
    logger = get_run_logger()
    
    # Schedule a flow to run in 1 hour
    future_time = datetime.now() + timedelta(hours=1)
    
    run = run_flow(
        'cleanup_job',
        parameters={'task': 'cleanup'},
        scheduled_start=future_time
    )
    
    if run:
        logger.info(f"Flow scheduled for {future_time}")
```

## 📚 Core Concepts

### The `@flow` Decorator

The `@flow` decorator is the main entry point for creating orchestrated workflows. It:

- Manages the flow lifecycle (status updates)
- Provides automatic logging
- Handles errors and reports them to the orchestrator
- Enables auto-execution when run directly

### Flow Context Functions

Access flow context using these helper functions:

- `get_run_logger()` - Get the logger instance
- `get_workspace_id()` - Get the current workspace ID
- `get_block(key_name)` - Retrieve a configuration block
- `run_flow(flow_name, ...)` - Trigger another flow

### Flow Triggering

Trigger flows in two ways:

1. **Using `.submit()` method** (recommended):
   ```python
   run = my_flow.submit(parameters={'key': 'value'})
   ```

2. **Using `run_flow()` function**:
   ```python
   run = run_flow('my_flow', parameters={'key': 'value'})
   ```

## 🔐 Secret Management

LastCron automatically redacts secret values from logs:

```python
from lastcron import flow, get_block, get_run_logger

@flow
def secure_flow(**params):
    logger = get_run_logger()
    
    # Get a secret block
    db_password = get_block('database-password')
    
    if db_password:
        # This will be redacted in logs: "Password: ****"
        logger.info(f"Password: {db_password.value}")
        
        # Use the actual value in your code
        connect_to_database(password=db_password.value)
```

## 🔄 Advanced Usage

### Asynchronous API Client

For high-performance applications, use the async client:

```python
from lastcron import AsyncAPIClient
import asyncio

async def main():
    async with AsyncAPIClient(token="your_token", base_url="http://localhost/api") as client:
        # Trigger multiple flows concurrently
        tasks = [
            client.trigger_flow_by_name(1, "flow_a"),
            client.trigger_flow_by_name(1, "flow_b"),
            client.trigger_flow_by_name(1, "flow_c")
        ]
        results = await asyncio.gather(*tasks)

asyncio.run(main())
```

### Type-Safe Data Classes

Use strongly-typed dataclasses for better IDE support:

```python
from lastcron import flow, get_run_logger, FlowRun, Block, BlockType

@flow
def typed_flow(**params):
    logger = get_run_logger()
    
    # Trigger a flow and get a typed response
    run: FlowRun = my_other_flow.submit(parameters={'key': 'value'})
    
    if run:
        logger.info(f"Run ID: {run.id}")
        logger.info(f"State: {run.state.value}")
    
    # Get a block with type information
    config: Block = get_block('config')
    if config and config.type == BlockType.JSON:
        logger.info("Got JSON configuration")
```

## 🛠️ Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/allanbru/lastcron-sdk.git
cd lastcron-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lastcron --cov-report=html

# Run specific test file
pytest tests/test_flow.py
```

### Code Quality

```bash
# Format code
black lastcron/

# Lint code
ruff check lastcron/

# Type check
mypy lastcron/
```

## 📖 Documentation

For detailed documentation, see:

- [SDK Documentation](lastcron/README.md) - Comprehensive SDK guide
- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Examples](examples/) - Example flows and use cases

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up your development environment
- Code style and standards
- Testing requirements
- Pull request process

## 📄 License

This project is licensed under the **Elastic License 2.0** - see the [LICENSE](LICENSE) file for details.

The Elastic License 2.0 is a source-available license that allows you to:
- Use the software freely
- Modify and distribute the software
- Use it in commercial applications

With the limitation that you cannot provide the software as a managed service.

## 🙏 Acknowledgments

Built with ❤️ by AllanBR Creations

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/allanbru/lastcron-sdk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/allanbru/lastcron-sdk/discussions)

## 🗺️ Roadmap

- [ ] Enhanced error handling and retry mechanisms
- [ ] Flow dependencies and DAG support
- [ ] Real-time flow monitoring
- [ ] Flow templates and reusable components
- [ ] Integration with popular data tools
- [ ] Web UI for flow visualization

---

**Note**: This SDK is designed to work with the LastCron orchestration platform. You'll need a running LastCron instance to execute flows.

