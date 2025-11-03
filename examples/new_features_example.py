"""
Example demonstrating the new LastCron SDK features:

1. Flow.submit() method - Trigger flows using the decorated function
2. get_block() function - Retrieve configuration blocks on-demand
3. Strong typing - All functions return typed dataclasses

These features make the SDK more intuitive and type-safe.
"""

from lastcron_sdk import flow, get_block, Block, FlowRun
from datetime import datetime, timedelta


# ============================================================================
# Example 1: Using .submit() to trigger flows
# ============================================================================

@flow
def data_extraction(logger, workspace_id, **params):
    """
    A flow that extracts data from a source.
    """
    parameters = params.get('parameters', {})
    source = parameters.get('source', 'database')
    
    logger.info(f"Extracting data from {source}")
    
    # Simulate data extraction
    logger.info("Data extraction completed")


@flow
def data_transformation(logger, workspace_id, **params):
    """
    A flow that transforms extracted data.
    """
    parameters = params.get('parameters', {})
    format_type = parameters.get('format', 'json')
    
    logger.info(f"Transforming data to {format_type} format")
    
    # Simulate data transformation
    logger.info("Data transformation completed")


@flow
def orchestrator_with_submit(logger, workspace_id, **params):
    """
    Example showing how to use .submit() to trigger flows.
    
    The .submit() method is cleaner than run_flow() because:
    - You reference the actual flow function
    - Better IDE autocomplete and type checking
    - More Pythonic and intuitive
    """
    logger.info("=== Orchestrator using .submit() ===")
    
    # Trigger flows using .submit() method
    # This is more intuitive than run_flow('flow_name')
    
    # 1. Trigger extraction immediately
    extraction_run: FlowRun = data_extraction.submit(
        parameters={'source': 'api', 'endpoint': '/data'}
    )
    
    if extraction_run:
        logger.info(f"✓ Triggered extraction: Run ID {extraction_run.id}")
        logger.info(f"  State: {extraction_run.state.value}")
        logger.info(f"  Flow ID: {extraction_run.flow_id}")
    
    # 2. Schedule transformation for later
    future_time = datetime.now() + timedelta(minutes=5)
    transform_run: FlowRun = data_transformation.submit(
        parameters={'format': 'parquet'},
        scheduled_start=future_time
    )
    
    if transform_run:
        logger.info(f"✓ Scheduled transformation: Run ID {transform_run.id}")
        logger.info(f"  Scheduled for: {transform_run.scheduled_start}")
    
    logger.info("Orchestration completed")


# ============================================================================
# Example 2: Using get_block() to retrieve configuration
# ============================================================================

@flow
def flow_with_blocks(logger, workspace_id, **params):
    """
    Example showing how to use get_block() to retrieve configuration.
    
    Benefits of get_block():
    - Fetch only the blocks you need
    - Returns a typed Block dataclass
    - Cleaner than parsing the blocks list
    - Secrets are automatically decrypted
    """
    logger.info("=== Flow using get_block() ===")
    
    # Get AWS credentials block
    aws_creds: Block = get_block('aws-credentials')
    
    if aws_creds:
        logger.info(f"✓ Got AWS credentials block")
        logger.info(f"  Key: {aws_creds.key_name}")
        logger.info(f"  Type: {aws_creds.type.value}")
        logger.info(f"  Is Secret: {aws_creds.is_secret}")
        logger.info(f"  Workspace ID: {aws_creds.workspace_id or 'Global'}")
        
        # The value is automatically decrypted if it was a secret
        # Use it directly in your code
        # credentials = json.loads(aws_creds.value)
    else:
        logger.warning("AWS credentials block not found")
    
    # Get API key block
    api_key: Block = get_block('api-key')
    
    if api_key:
        logger.info(f"✓ Got API key block")
        # Use the API key
        # headers = {'Authorization': f'Bearer {api_key.value}'}
    else:
        logger.warning("API key block not found")
    
    # Get database config block
    db_config: Block = get_block('database-config')
    
    if db_config:
        logger.info(f"✓ Got database config")
        logger.info(f"  Type: {db_config.type.value}")
        # Parse JSON config
        # config = json.loads(db_config.value)
    
    logger.info("Block retrieval completed")


# ============================================================================
# Example 3: Combining .submit() and get_block()
# ============================================================================

@flow
def api_data_fetcher(logger, workspace_id, **params):
    """
    Fetches data from an API using credentials from blocks.
    """
    parameters = params.get('parameters', {})
    endpoint = parameters.get('endpoint', '/data')
    
    logger.info(f"Fetching data from {endpoint}")
    
    # Get API credentials
    api_creds: Block = get_block('api-credentials')
    
    if not api_creds:
        logger.error("API credentials not found!")
        return
    
    logger.info("Using API credentials to fetch data")
    # In real code: requests.get(endpoint, headers={'Authorization': api_creds.value})
    
    logger.info("Data fetched successfully")


@flow
def database_loader(logger, workspace_id, **params):
    """
    Loads data into a database using credentials from blocks.
    """
    parameters = params.get('parameters', {})
    table = parameters.get('table', 'data')
    
    logger.info(f"Loading data into table: {table}")
    
    # Get database credentials
    db_creds: Block = get_block('database-credentials')
    
    if not db_creds:
        logger.error("Database credentials not found!")
        return
    
    logger.info("Using database credentials to load data")
    # In real code: connect to database and load data
    
    logger.info("Data loaded successfully")


@flow
def etl_pipeline(logger, workspace_id, **params):
    """
    Complete ETL pipeline using .submit() and get_block().
    
    This demonstrates a real-world use case combining both features.
    """
    logger.info("=== ETL Pipeline ===")
    
    # Get pipeline configuration
    pipeline_config: Block = get_block('pipeline-config')
    
    if pipeline_config:
        logger.info(f"Pipeline config: {pipeline_config.type.value}")
        # config = json.loads(pipeline_config.value)
        # batch_size = config.get('batch_size', 1000)
    
    # Step 1: Fetch data from API
    logger.info("Step 1: Triggering API data fetch")
    fetch_run: FlowRun = api_data_fetcher.submit(
        parameters={'endpoint': '/api/v1/data'}
    )
    
    if fetch_run:
        logger.info(f"✓ Fetch triggered: {fetch_run.id}")
    
    # Step 2: Schedule database load for later
    # In a real pipeline, you'd wait for the fetch to complete
    # or use a workflow orchestration pattern
    logger.info("Step 2: Scheduling database load")
    load_time = datetime.now() + timedelta(minutes=2)
    load_run: FlowRun = database_loader.submit(
        parameters={'table': 'staging_data'},
        scheduled_start=load_time
    )
    
    if load_run:
        logger.info(f"✓ Load scheduled: {load_run.id}")
        logger.info(f"  Will run at: {load_run.scheduled_start}")
    
    logger.info("ETL pipeline orchestration completed")


# ============================================================================
# Example 4: Type-safe flow orchestration
# ============================================================================

@flow
def type_safe_orchestrator(logger, workspace_id, **params):
    """
    Example showing type safety benefits.
    
    With typed returns, your IDE can:
    - Autocomplete FlowRun attributes
    - Catch type errors before runtime
    - Provide better documentation
    """
    logger.info("=== Type-Safe Orchestrator ===")
    
    # Trigger a flow - returns FlowRun (not Dict)
    run: FlowRun = data_extraction.submit(
        parameters={'source': 'database'}
    )
    
    if run:
        # IDE knows these attributes exist and their types
        logger.info(f"Run ID: {run.id}")  # int
        logger.info(f"Flow ID: {run.flow_id}")  # int
        logger.info(f"State: {run.state}")  # FlowRunState enum
        logger.info(f"Parameters: {run.parameters}")  # Dict[str, Any]
        
        # Can check state using enum
        from lastcron_sdk import FlowRunState
        if run.state == FlowRunState.PENDING:
            logger.info("Run is pending")
    
    # Get a block - returns Block (not Dict)
    block: Block = get_block('my-config')
    
    if block:
        # IDE knows these attributes exist and their types
        logger.info(f"Block key: {block.key_name}")  # str
        logger.info(f"Block type: {block.type}")  # BlockType enum
        logger.info(f"Is secret: {block.is_secret}")  # bool
        logger.info(f"Value: {block.value}")  # str
        
        # Can check type using enum
        from lastcron_sdk import BlockType
        if block.type == BlockType.JSON:
            logger.info("Block contains JSON data")
            # import json
            # data = json.loads(block.value)
    
    logger.info("Type-safe orchestration completed")


# ============================================================================
# Example 5: Error handling with typed returns
# ============================================================================

@flow
def error_handling_example(logger, workspace_id, **params):
    """
    Example showing error handling with typed returns.
    """
    logger.info("=== Error Handling Example ===")
    
    # Try to get a block that might not exist
    config: Block = get_block('optional-config')
    
    if config is None:
        logger.warning("Optional config not found, using defaults")
        # Use default configuration
    else:
        logger.info(f"Using config: {config.key_name}")
    
    # Try to trigger a flow that might not exist
    run: FlowRun = data_extraction.submit(
        parameters={'source': 'unknown'}
    )
    
    if run is None:
        logger.error("Failed to trigger flow")
        # Handle the error
    else:
        logger.info(f"Flow triggered successfully: {run.id}")
    
    logger.info("Error handling completed")

