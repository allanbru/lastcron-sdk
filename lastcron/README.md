# LastCron SDK

Python SDK for building flows that run in the LastCron orchestrator.

## Features

- **Flow Decorator**: Simple `@flow` decorator to mark functions as orchestrated flows
- **Flow.submit() Method**: Trigger flows by calling the decorated function directly ⭐ NEW
- **Automatic Logging**: Built-in logger that sends logs back to the orchestrator
- **Parameter Injection**: Automatic injection of parameters, blocks, logger, and workspace_id
- **Block Retrieval**: On-demand block fetching with `get_block()` function ⭐ NEW
- **Flow Triggering**: Trigger other flows programmatically with `run_flow()` or `.submit()`
- **Input Validation**: Automatic validation of timestamps, parameters, and flow names
- **Strong Typing**: Type-safe dataclasses for all API responses ⭐ NEW
- **Sync & Async Clients**: Both synchronous and asynchronous API clients available

## Installation

The SDK is included in your workspace repository. Import it in your Python flows:

```python
from lastcron import flow, run_flow, get_block
from lastcron import Block, FlowRun, BlockType, FlowRunState
from lastcron import APIClient, AsyncAPIClient
```

## Quick Start

### Basic Flow

```python
from lastcron import flow

@flow
def my_flow(logger, workspace_id, **params):
    logger.info(f"Flow started in workspace {workspace_id}")

    # Your flow logic here
    parameters = params.get('parameters', {})
    logger.info(f"Parameters: {parameters}")

    logger.info("Flow completed")
```

### Triggering Other Flows (New .submit() Method)

```python
from lastcron import flow, FlowRun
from datetime import datetime, timedelta

@flow
def data_processing(logger, workspace_id, **params):
    logger.info("Processing data...")

@flow
def orchestrator(logger, workspace_id, **params):
    # Trigger using .submit() method (recommended)
    run: FlowRun = data_processing.submit(
        parameters={'batch_size': 100}
    )

    if run:
        logger.info(f"Triggered run ID: {run.id}")

    # Or use run_flow() (still works)
    run = run_flow('data_processing', parameters={'batch_size': 100})
```

### Retrieving Configuration Blocks

```python
from lastcron import flow, get_block, Block

@flow
def my_flow(logger, workspace_id, **params):
    # Get a configuration block on-demand
    api_key: Block = get_block('api-key')

    if api_key:
        logger.info(f"Got API key: {api_key.key_name}")
        # Use the value (automatically decrypted if secret)
        # headers = {'Authorization': f'Bearer {api_key.value}'}
```

## Core Concepts

### The `@flow` Decorator

The `@flow` decorator is the main entry point for your flows. It handles:
- Fetching run parameters and configuration blocks
- Managing flow lifecycle (status updates)
- Providing a logger for tracking execution
- Handling errors and reporting them back to the orchestrator

### Basic Flow Example

```python
from lastcron import flow

@flow
def my_flow(logger, workspace_id, **params):
    """
    A simple flow that processes data.

    The flow decorator automatically injects:
    - logger: OrchestratorLogger instance for logging
    - workspace_id: The ID of the workspace this flow belongs to
    - **params: All other parameters including 'parameters' and 'blocks'
    """
    logger.info(f"Flow started in workspace {workspace_id}")

    # Access parameters
    batch_size = params.get('parameters', {}).get('batch_size', 100)
    logger.info(f"Processing with batch size: {batch_size}")
    
    # Your flow logic here
    result = process_data(batch_size)
    
    logger.info(f"Flow completed. Processed {result} items")
```

## Triggering Other Flows

The `run_flow()` function allows you to programmatically trigger other flows in the same workspace from within your flow.

**Important:** The `workspace_id` is automatically determined from the current flow context, so you don't need to pass it manually. Just call `run_flow()` with the flow name and optional parameters.

### Function Signature

```python
def run_flow(
    flow_name: str,
    parameters: Optional[Dict[str, Any]] = None,
    scheduled_start: Optional[Union[str, datetime]] = None
) -> Optional[Dict[str, Any]]
```

### Parameters

- **flow_name** (str, required): The name of the flow to trigger (must exist in the same workspace)
  - Flow names are case-sensitive and must match exactly
  - Automatically validated and trimmed
- **parameters** (dict, optional): Dictionary of parameters to pass to the triggered flow
  - Must be a valid dictionary (validated automatically)
  - Can be `None` for no parameters
- **scheduled_start** (datetime or str, optional): When to start the flow
  - If `None`: Flow starts immediately
  - If `datetime`: Flow starts at the specified time (validated to be in the future)
  - If `str`: ISO format datetime string (e.g., "2024-11-02T15:30:00")
  - **Validation**: Timestamps are automatically validated to ensure they're in the future

### Return Value

Returns a dictionary with the created flow run details:
```python
{
    'id': 123,                    # The run ID
    'flow_id': 45,                # The ID of the triggered flow
    'state': 'PENDING',           # Initial state
    'parameters': {...},          # Parameters passed to the run
    'scheduled_start': '...',     # When the run is scheduled
    'created_at': '...',
    'updated_at': '...'
}
```

Returns `None` if the trigger request failed.

### Examples

#### Example 1: Trigger a Flow Immediately

```python
from lastcron import flow, run_flow

@flow
def data_pipeline(logger, **params):
    logger.info("Starting data pipeline")
    
    # Process data
    data = extract_data()
    transformed = transform_data(data)
    load_data(transformed)
    
    # Trigger the cleanup flow after processing
    logger.info("Triggering cleanup flow")
    run = run_flow('cleanup_job')
    
    if run:
        logger.info(f"Cleanup flow triggered successfully. Run ID: {run['id']}")
    else:
        logger.error("Failed to trigger cleanup flow")
```

#### Example 2: Trigger with Parameters

```python
from lastcron import flow, run_flow

@flow
def orchestrator_flow(logger, **params):
    logger.info("Orchestrating multiple flows")
    
    # Trigger data processing with specific parameters
    run = run_flow(
        'data_processing',
        parameters={
            'batch_size': 1000,
            'source': 'database_a',
            'target': 'warehouse'
        }
    )
    
    if run:
        logger.info(f"Data processing started: {run['id']}")
```

#### Example 3: Schedule a Flow for Later

```python
from lastcron import flow, run_flow
from datetime import datetime, timedelta

@flow
def scheduler_flow(logger, **params):
    logger.info("Scheduling future flows")
    
    # Schedule a flow to run in 1 hour
    future_time = datetime.now() + timedelta(hours=1)
    
    run = run_flow(
        'delayed_job',
        parameters={'task': 'cleanup'},
        scheduled_start=future_time
    )
    
    if run:
        logger.info(f"Flow scheduled for {future_time}")
```

#### Example 4: Chain Multiple Flows

```python
from lastcron import flow, run_flow

@flow
def etl_orchestrator(logger, **params):
    """
    Orchestrates a multi-stage ETL pipeline by triggering flows in sequence.
    """
    logger.info("Starting ETL orchestration")
    
    # Stage 1: Extract
    extract_run = run_flow('extract_data', parameters={'source': 'api'})
    if not extract_run:
        logger.error("Failed to trigger extract flow")
        return
    
    logger.info(f"Extract flow triggered: {extract_run['id']}")
    
    # Stage 2: Transform (scheduled to run after extract completes)
    from datetime import datetime, timedelta
    transform_time = datetime.now() + timedelta(minutes=30)
    
    transform_run = run_flow(
        'transform_data',
        parameters={'extract_run_id': extract_run['id']},
        scheduled_start=transform_time
    )
    
    if transform_run:
        logger.info(f"Transform flow scheduled: {transform_run['id']}")
    
    # Stage 3: Load
    load_time = datetime.now() + timedelta(hours=1)
    load_run = run_flow(
        'load_data',
        parameters={'transform_run_id': transform_run['id']},
        scheduled_start=load_time
    )
    
    if load_run:
        logger.info(f"Load flow scheduled: {load_run['id']}")
    
    logger.info("ETL pipeline orchestration complete")
```

#### Example 5: Conditional Flow Triggering

```python
from lastcron import flow, run_flow

@flow
def data_quality_check(logger, **params):
    """
    Checks data quality and triggers different flows based on results.
    """
    logger.info("Running data quality checks")
    
    # Run quality checks
    quality_score = check_data_quality()
    logger.info(f"Quality score: {quality_score}")
    
    if quality_score >= 0.95:
        # High quality - proceed with production pipeline
        logger.info("Quality check passed - triggering production pipeline")
        run_flow('production_pipeline', parameters={'quality_score': quality_score})
    elif quality_score >= 0.80:
        # Medium quality - trigger data cleaning
        logger.warning("Quality check marginal - triggering data cleaning")
        run_flow('data_cleaning', parameters={'quality_score': quality_score})
    else:
        # Low quality - trigger alert and investigation
        logger.error("Quality check failed - triggering alert")
        run_flow('quality_alert', parameters={
            'quality_score': quality_score,
            'severity': 'high'
        })
```

## Logging

The logger is automatically provided to your flow function:

```python
@flow
def my_flow(logger, **params):
    logger.info("Informational message")
    logger.warning("Warning message")
    logger.error("Error message")
```

All logs are sent to the orchestrator and can be viewed in the web UI.

## Error Handling

The `@flow` decorator automatically catches exceptions and reports them to the orchestrator:

```python
@flow
def my_flow(logger, **params):
    logger.info("Starting risky operation")
    
    try:
        risky_operation()
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        # The flow will be marked as FAILED
        raise  # Re-raise to ensure proper error reporting
```

## Best Practices

1. **Always use the logger**: Don't use `print()` - use the provided logger so messages are captured
2. **Handle errors gracefully**: Catch expected errors and log them appropriately
3. **Use parameters**: Make flows configurable through parameters rather than hardcoding values
4. **Check return values**: When using `run_flow()`, always check if the return value is `None`
5. **Schedule wisely**: When scheduling flows, ensure you account for the expected duration of prerequisite flows
6. **Keep flows focused**: Each flow should do one thing well - use `run_flow()` to orchestrate complex workflows

## Advanced: Direct API Access

For advanced use cases, you can use the `APIClient` or `AsyncAPIClient` directly to interact with the orchestrator API.

### Synchronous API Client

```python
from lastcron import APIClient

# Initialize with your authentication token
client = APIClient(token="your_token", base_url="http://localhost/api")

# Trigger a flow by name
run = client.trigger_flow_by_name(
    workspace_id=1,
    flow_name="my_flow",
    parameters={"key": "value"}
)

# Get flow runs
runs = client.get_flow_runs(flow_id=5, limit=10)

# Get run logs
logs = client.get_run_logs(run_id=123)
```

### Asynchronous API Client

```python
from lastcron import AsyncAPIClient
import asyncio

async def main():
    # Use as context manager
    async with AsyncAPIClient(token="your_token", base_url="http://localhost/api") as client:
        # Trigger multiple flows concurrently
        tasks = [
            client.trigger_flow_by_name(1, "flow_a"),
            client.trigger_flow_by_name(1, "flow_b"),
            client.trigger_flow_by_name(1, "flow_c")
        ]
        results = await asyncio.gather(*tasks)

        # Get flow details
        flow = await client.get_flow_by_name(workspace_id=1, flow_name="my_flow")
        print(f"Flow ID: {flow['id']}")

asyncio.run(main())
```

### Available API Methods

Both `APIClient` and `AsyncAPIClient` provide:

**Orchestrator Endpoints:**
- `get_run_details(run_id)` - Get run details
- `update_run_status(run_id, state, message, exit_code)` - Update run status
- `send_log_entry(run_id, log_entry)` - Send log entry

**V1 API Endpoints:**
- `list_workspace_flows(workspace_id)` - List all flows in workspace
- `get_flow_by_name(workspace_id, flow_name)` - Find flow by name
- `trigger_flow_by_id(flow_id, parameters, scheduled_start)` - Trigger by ID
- `trigger_flow_by_name(workspace_id, flow_name, parameters, scheduled_start)` - Trigger by name
- `get_flow_runs(flow_id, limit)` - Get run history
- `get_run_logs(run_id)` - Get run logs

## Input Validation

The SDK automatically validates all inputs:

### Timestamp Validation

```python
from datetime import datetime, timedelta

# ✅ Valid: Future datetime
future = datetime.now() + timedelta(hours=1)
run_flow('my_flow', scheduled_start=future)

# ✅ Valid: ISO format string
run_flow('my_flow', scheduled_start='2024-11-02T15:30:00')

# ✅ Valid: None (immediate execution)
run_flow('my_flow', scheduled_start=None)

# ❌ Invalid: Past datetime (raises ValueError)
past = datetime.now() - timedelta(hours=1)
run_flow('my_flow', scheduled_start=past)  # ValueError!

# ❌ Invalid: Bad format (raises ValueError)
run_flow('my_flow', scheduled_start='2024/11/02')  # ValueError!
```

### Parameter Validation

```python
# ✅ Valid: Dictionary
run_flow('my_flow', parameters={'key': 'value'})

# ✅ Valid: None
run_flow('my_flow', parameters=None)

# ❌ Invalid: Not a dictionary (raises TypeError)
run_flow('my_flow', parameters="invalid")  # TypeError!
```

### Flow Name Validation

```python
# ✅ Valid: Normal flow name
run_flow('data_processing')

# ✅ Valid: Whitespace is trimmed
run_flow('  my_flow  ')  # Becomes 'my_flow'

# ❌ Invalid: Empty string (raises ValueError)
run_flow('')  # ValueError!

# ❌ Invalid: Too long (raises ValueError)
run_flow('a' * 300)  # ValueError!
```

## Error Handling

The SDK provides comprehensive error handling:

```python
from lastcron import flow, run_flow

@flow
def my_flow(logger, **params):
    try:
        # This will raise ValueError if flow doesn't exist
        run = run_flow('nonexistent_flow')
    except ValueError as e:
        logger.error(f"Flow not found: {e}")
        return

    try:
        # This will raise ValueError if timestamp is in the past
        from datetime import datetime, timedelta
        past = datetime.now() - timedelta(hours=1)
        run = run_flow('my_flow', scheduled_start=past)
    except ValueError as e:
        logger.error(f"Invalid timestamp: {e}")
        return

    try:
        # This will raise TypeError if parameters are invalid
        run = run_flow('my_flow', parameters="not a dict")
    except TypeError as e:
        logger.error(f"Invalid parameters: {e}")
        return
```

## Limitations

- `run_flow()` can only trigger flows in the same workspace
- Flows are triggered asynchronously - the calling flow doesn't wait for completion
- You cannot directly pass large data between flows - use shared storage or databases
- The flow name must match exactly (case-sensitive)
- Scheduled times must be in the future (validated automatically)

