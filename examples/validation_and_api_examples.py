"""
Example: Input Validation and Direct API Access

This example demonstrates:
1. Automatic input validation for run_flow()
2. Using the APIClient directly for advanced use cases
3. Using the AsyncAPIClient for concurrent operations
4. Proper error handling
5. Automatic workspace_id injection in flow context

Note: The workspace_id is automatically injected by the @flow decorator
and is available as a parameter in your flow function. It's also used
internally by run_flow() to trigger flows in the same workspace.
"""

from lastcron_sdk import flow, run_flow, APIClient, AsyncAPIClient
from datetime import datetime, timedelta
import asyncio


# ============================================================================
# Example 1: Timestamp Validation
# ============================================================================

@flow
def timestamp_validation_example(logger, workspace_id, **params):
    """
    Demonstrates automatic timestamp validation.

    Note: workspace_id is automatically injected and used by run_flow()
    """
    logger.info("=== Timestamp Validation Example ===")
    logger.info(f"Running in workspace {workspace_id}")

    # ✅ Valid: Future datetime
    logger.info("Test 1: Future datetime")
    future = datetime.now() + timedelta(hours=1)
    run = run_flow('test_flow', scheduled_start=future)
    if run:
        logger.info(f"  ✓ Scheduled for {future}")
    
    # ✅ Valid: ISO format string
    logger.info("Test 2: ISO format string")
    iso_time = (datetime.now() + timedelta(hours=2)).isoformat()
    run = run_flow('test_flow', scheduled_start=iso_time)
    if run:
        logger.info(f"  ✓ Scheduled for {iso_time}")
    
    # ✅ Valid: None (immediate)
    logger.info("Test 3: Immediate execution (None)")
    run = run_flow('test_flow', scheduled_start=None)
    if run:
        logger.info("  ✓ Triggered immediately")
    
    # ❌ Invalid: Past datetime
    logger.info("Test 4: Past datetime (should fail)")
    try:
        past = datetime.now() - timedelta(hours=1)
        run = run_flow('test_flow', scheduled_start=past)
        logger.error("  ✗ Should have raised ValueError!")
    except ValueError as e:
        logger.info(f"  ✓ Correctly rejected: {e}")
    
    # ❌ Invalid: Bad format
    logger.info("Test 5: Invalid format (should fail)")
    try:
        run = run_flow('test_flow', scheduled_start='2024/11/02')
        logger.error("  ✗ Should have raised ValueError!")
    except ValueError as e:
        logger.info(f"  ✓ Correctly rejected: {e}")


# ============================================================================
# Example 2: Parameter Validation
# ============================================================================

@flow
def parameter_validation_example(logger, workspace_id, **params):
    """
    Demonstrates automatic parameter validation.
    """
    logger.info("=== Parameter Validation Example ===")
    logger.info(f"Running in workspace {workspace_id}")

    # ✅ Valid: Dictionary
    logger.info("Test 1: Valid dictionary")
    run = run_flow('test_flow', parameters={'key': 'value', 'count': 42})
    if run:
        logger.info("  ✓ Parameters accepted")
    
    # ✅ Valid: None
    logger.info("Test 2: None parameters")
    run = run_flow('test_flow', parameters=None)
    if run:
        logger.info("  ✓ None accepted")
    
    # ✅ Valid: Empty dictionary
    logger.info("Test 3: Empty dictionary")
    run = run_flow('test_flow', parameters={})
    if run:
        logger.info("  ✓ Empty dict accepted")
    
    # ❌ Invalid: String instead of dict
    logger.info("Test 4: String instead of dict (should fail)")
    try:
        run = run_flow('test_flow', parameters="invalid")
        logger.error("  ✗ Should have raised TypeError!")
    except TypeError as e:
        logger.info(f"  ✓ Correctly rejected: {e}")
    
    # ❌ Invalid: List instead of dict
    logger.info("Test 5: List instead of dict (should fail)")
    try:
        run = run_flow('test_flow', parameters=['a', 'b', 'c'])
        logger.error("  ✗ Should have raised TypeError!")
    except TypeError as e:
        logger.info(f"  ✓ Correctly rejected: {e}")


# ============================================================================
# Example 3: Flow Name Validation
# ============================================================================

@flow
def flow_name_validation_example(logger, workspace_id, **params):
    """
    Demonstrates flow name validation and lookup.
    """
    logger.info("=== Flow Name Validation Example ===")
    logger.info(f"Running in workspace {workspace_id}")

    # ✅ Valid: Normal flow name
    logger.info("Test 1: Valid flow name")
    run = run_flow('data_processing')
    if run:
        logger.info("  ✓ Flow found and triggered")
    else:
        logger.warning("  ⚠ Flow not found (expected if it doesn't exist)")
    
    # ✅ Valid: Whitespace is trimmed
    logger.info("Test 2: Flow name with whitespace")
    run = run_flow('  data_processing  ')
    if run:
        logger.info("  ✓ Whitespace trimmed, flow triggered")
    
    # ❌ Invalid: Empty string
    logger.info("Test 3: Empty flow name (should fail)")
    try:
        run = run_flow('')
        logger.error("  ✗ Should have raised ValueError!")
    except ValueError as e:
        logger.info(f"  ✓ Correctly rejected: {e}")
    
    # ❌ Invalid: Nonexistent flow
    logger.info("Test 4: Nonexistent flow")
    run = run_flow('this_flow_does_not_exist_12345')
    if run is None:
        logger.info("  ✓ Correctly returned None for nonexistent flow")


# ============================================================================
# Example 4: Using APIClient Directly
# ============================================================================

@flow
def api_client_example(logger, workspace_id, **params):
    """
    Demonstrates using the APIClient directly for advanced operations.

    Note: workspace_id is automatically available from the flow context
    """
    logger.info("=== Direct API Client Example ===")
    logger.info(f"Running in workspace {workspace_id}")

    # Get the API token and base URL from environment
    import os
    token = os.environ.get('ORCH_TOKEN')
    api_base = os.environ.get('ORCH_API_BASE_URL')

    if not token or not api_base:
        logger.error("Cannot access API credentials")
        return

    # Create API client
    client = APIClient(token=token, base_url=api_base.replace('/orchestrator', ''))

    # Example 1: List all flows in workspace
    logger.info("Listing all flows in workspace...")
    # Use workspace_id from flow context instead of params
    flows = client.list_workspace_flows(workspace_id)
    
    if flows:
        logger.info(f"Found {len(flows)} flows:")
        for flow in flows[:5]:  # Show first 5
            logger.info(f"  - {flow['name']} (ID: {flow['id']})")
    
    # Example 2: Get specific flow by name
    logger.info("Looking up flow by name...")
    flow = client.get_flow_by_name(workspace_id, 'data_processing')
    if flow:
        logger.info(f"Found flow: {flow['name']} (ID: {flow['id']})")
    
    # Example 3: Trigger flow by ID
    if flow:
        logger.info("Triggering flow by ID...")
        run = client.trigger_flow_by_id(
            flow['id'],
            parameters={'source': 'api_client_example'},
            scheduled_start=datetime.now() + timedelta(minutes=5)
        )
        if run:
            logger.info(f"Triggered run ID: {run['id']}")
    
    # Example 4: Get run history
    if flow:
        logger.info("Getting run history...")
        runs = client.get_flow_runs(flow['id'], limit=5)
        if runs:
            logger.info(f"Last {len(runs)} runs:")
            for run in runs:
                logger.info(f"  - Run {run['id']}: {run['state']}")


# ============================================================================
# Example 5: Using AsyncAPIClient for Concurrent Operations
# ============================================================================

@flow
def async_api_client_example(logger, workspace_id, **params):
    """
    Demonstrates using AsyncAPIClient for concurrent operations.
    Note: This requires running in an async context.

    Note: workspace_id is automatically available from the flow context
    """
    logger.info("=== Async API Client Example ===")
    logger.info(f"Running in workspace {workspace_id}")

    import os
    token = os.environ.get('ORCH_TOKEN')
    api_base = os.environ.get('ORCH_API_BASE_URL')

    if not token or not api_base:
        logger.error("Cannot access API credentials")
        return

    async def trigger_multiple_flows():
        """Trigger multiple flows concurrently."""
        async with AsyncAPIClient(token=token, base_url=api_base.replace('/orchestrator', '')) as client:
            
            # Get all flows first
            flows = await client.list_workspace_flows(workspace_id)
            logger.info(f"Found {len(flows) if flows else 0} flows")
            
            if not flows or len(flows) < 3:
                logger.warning("Need at least 3 flows for this example")
                return
            
            # Trigger first 3 flows concurrently
            logger.info("Triggering 3 flows concurrently...")
            tasks = []
            for flow in flows[:3]:
                task = client.trigger_flow_by_id(
                    flow['id'],
                    parameters={'triggered_by': 'async_example'}
                )
                tasks.append(task)
            
            # Wait for all to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Flow {i+1} failed: {result}")
                elif result:
                    logger.info(f"Flow {i+1} triggered: Run ID {result['id']}")
                else:
                    logger.warning(f"Flow {i+1} returned None")
    
    # Run the async function
    try:
        asyncio.run(trigger_multiple_flows())
        logger.info("Async operations completed")
    except Exception as e:
        logger.error(f"Async operations failed: {e}")


# ============================================================================
# Example 6: Comprehensive Error Handling
# ============================================================================

@flow
def comprehensive_error_handling(logger, workspace_id, **params):
    """
    Demonstrates comprehensive error handling for all validation scenarios.
    """
    logger.info("=== Comprehensive Error Handling ===")
    logger.info(f"Running in workspace {workspace_id}")

    def safe_trigger(flow_name, parameters=None, scheduled_start=None):
        """Safely trigger a flow with full error handling."""
        try:
            run = run_flow(flow_name, parameters=parameters, scheduled_start=scheduled_start)
            
            if run:
                logger.info(f"✓ Successfully triggered '{flow_name}': Run ID {run['id']}")
                return run
            else:
                logger.warning(f"⚠ Failed to trigger '{flow_name}': API returned None")
                return None
                
        except ValueError as e:
            logger.error(f"✗ Validation error for '{flow_name}': {e}")
            return None
        except TypeError as e:
            logger.error(f"✗ Type error for '{flow_name}': {e}")
            return None
        except Exception as e:
            logger.error(f"✗ Unexpected error for '{flow_name}': {e}")
            return None
    
    # Test various scenarios
    logger.info("Test 1: Valid flow")
    safe_trigger('test_flow', parameters={'test': True})
    
    logger.info("Test 2: Invalid parameters")
    safe_trigger('test_flow', parameters="invalid")
    
    logger.info("Test 3: Past timestamp")
    safe_trigger('test_flow', scheduled_start=datetime.now() - timedelta(hours=1))
    
    logger.info("Test 4: Nonexistent flow")
    safe_trigger('nonexistent_flow_xyz')
    
    logger.info("Test 5: Valid scheduled flow")
    safe_trigger('test_flow', scheduled_start=datetime.now() + timedelta(hours=1))
    
    logger.info("All error handling tests completed")

