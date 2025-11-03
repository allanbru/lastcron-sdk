"""
Example: Auto-Execution Flow

This demonstrates the new auto-execution feature where flows can be run
directly without needing orchestrator_wrapper.py or python -m lastcron_sdk.

The @flow decorator automatically detects if:
1. The script is being run directly (python flow_file.py)
2. Orchestration environment variables are present (ORCH_RUN_ID, etc.)

If both conditions are met, the flow executes automatically!
"""

from lastcron_sdk import flow

@flow
def data_processing(logger, workspace_id, **params):
    """
    A simple data processing flow.
    
    This flow can be executed in multiple ways:
    
    1. By the Laravel orchestrator (automatic):
       - Laravel sets environment variables
       - Laravel runs: python3 flows/data_processing.py
       - The @flow decorator detects the env vars and executes automatically
    
    2. Manually for testing (if you set env vars):
       export ORCH_RUN_ID=123
       export ORCH_TOKEN=test_token
       export ORCH_API_BASE_URL=http://localhost/api/orchestrator/
       python3 data_processing.py
    
    3. From another flow:
       run = data_processing.submit(parameters={'batch_size': 100})
    """
    logger.info("Starting data processing flow")
    logger.info(f"Running in workspace: {workspace_id}")
    
    # Get parameters
    batch_size = params.get('parameters', {}).get('batch_size', 50)
    logger.info(f"Processing with batch size: {batch_size}")
    
    # Simulate processing
    for i in range(3):
        logger.info(f"Processing batch {i+1}...")
    
    logger.info("Data processing complete!")


# No need for this anymore!
# if __name__ == '__main__':
#     # The @flow decorator handles execution automatically
#     pass

# The flow will execute automatically if:
# - This file is run directly (python data_processing.py)
# - Environment variables are set (ORCH_RUN_ID, ORCH_TOKEN, ORCH_API_BASE_URL)
#
# Otherwise, the flow is just registered and can be imported/triggered by other flows.

