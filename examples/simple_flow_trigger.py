"""
Simple example showing workspace_id automatic injection and flow triggering.

This demonstrates the key improvement: workspace_id is automatically available
in the flow context and used by run_flow() without manual input.
"""

from lastcron_sdk import flow, run_flow
from datetime import datetime, timedelta


@flow
def orchestrator_flow(logger, workspace_id, **params):
    """
    A simple orchestrator flow that triggers other flows.
    
    Args:
        logger: Automatically injected logger
        workspace_id: Automatically injected workspace ID
        **params: Other parameters including 'parameters' and 'blocks'
    """
    logger.info(f"Orchestrator flow started in workspace {workspace_id}")
    
    # Extract parameters
    parameters = params.get('parameters', {})
    mode = parameters.get('mode', 'sequential')
    
    logger.info(f"Running in {mode} mode")
    
    if mode == 'sequential':
        # Trigger flows one after another
        logger.info("Triggering flows sequentially...")
        
        # Step 1: Data extraction
        run1 = run_flow('extract_data', parameters={'source': 'database'})
        if run1:
            logger.info(f"✓ Triggered extract_data: Run ID {run1['id']}")
        
        # Step 2: Data transformation
        run2 = run_flow('transform_data', parameters={'format': 'json'})
        if run2:
            logger.info(f"✓ Triggered transform_data: Run ID {run2['id']}")
        
        # Step 3: Data loading
        run3 = run_flow('load_data', parameters={'destination': 's3'})
        if run3:
            logger.info(f"✓ Triggered load_data: Run ID {run3['id']}")
    
    elif mode == 'scheduled':
        # Schedule flows for later
        logger.info("Scheduling flows for later execution...")
        
        # Schedule extract for 5 minutes from now
        extract_time = datetime.now() + timedelta(minutes=5)
        run1 = run_flow('extract_data', 
                       parameters={'source': 'api'},
                       scheduled_start=extract_time)
        if run1:
            logger.info(f"✓ Scheduled extract_data for {extract_time}")
        
        # Schedule transform for 10 minutes from now
        transform_time = datetime.now() + timedelta(minutes=10)
        run2 = run_flow('transform_data',
                       parameters={'format': 'parquet'},
                       scheduled_start=transform_time)
        if run2:
            logger.info(f"✓ Scheduled transform_data for {transform_time}")
    
    elif mode == 'conditional':
        # Conditional flow triggering based on parameters
        logger.info("Triggering flows conditionally...")
        
        data_source = parameters.get('data_source', 'database')
        
        if data_source == 'database':
            run = run_flow('extract_from_database', 
                          parameters={'table': parameters.get('table', 'users')})
            if run:
                logger.info(f"✓ Triggered database extraction: Run ID {run['id']}")
        
        elif data_source == 'api':
            run = run_flow('extract_from_api',
                          parameters={'endpoint': parameters.get('endpoint', '/data')})
            if run:
                logger.info(f"✓ Triggered API extraction: Run ID {run['id']}")
        
        else:
            logger.warning(f"Unknown data source: {data_source}")
    
    else:
        logger.error(f"Unknown mode: {mode}")
    
    logger.info("Orchestrator flow completed")


@flow
def simple_trigger_example(logger, workspace_id, **params):
    """
    Simplest possible example of triggering a flow.
    """
    logger.info(f"Simple trigger example in workspace {workspace_id}")
    
    # Just trigger another flow - that's it!
    run = run_flow('my_other_flow')
    
    if run:
        logger.info(f"Success! Triggered run ID: {run['id']}")
    else:
        logger.error("Failed to trigger flow")


@flow
def error_handling_example(logger, workspace_id, **params):
    """
    Example showing proper error handling when triggering flows.
    """
    logger.info(f"Error handling example in workspace {workspace_id}")
    
    # Try to trigger a flow that might not exist
    flow_name = params.get('parameters', {}).get('target_flow', 'nonexistent_flow')
    
    logger.info(f"Attempting to trigger: {flow_name}")
    run = run_flow(flow_name)
    
    if run:
        logger.info(f"✓ Successfully triggered {flow_name}")
        logger.info(f"  Run ID: {run['id']}")
        logger.info(f"  State: {run['state']}")
    else:
        logger.warning(f"⚠ Failed to trigger {flow_name}")
        logger.warning("This could mean:")
        logger.warning("  - Flow doesn't exist in this workspace")
        logger.warning("  - API error occurred")
        logger.warning("  - Validation failed")
        
        # Fallback: trigger a default flow
        logger.info("Triggering fallback flow instead...")
        fallback_run = run_flow('default_flow')
        if fallback_run:
            logger.info(f"✓ Fallback flow triggered: Run ID {fallback_run['id']}")

