# lastcron_sdk/flow.py

import functools
import sys
import os
from typing import Dict, Any, Optional
import traceback
from .logger import OrchestratorLogger
from .client import OrchestratorClient

# Global instances will be set by the wrapper
CLIENT: Optional[OrchestratorClient] = None
LOGGER: Optional[OrchestratorLogger] = None

def flow(func):
    """
    The core LastCron decorator. 
    It wraps the user's primary function, manages the run lifecycle, 
    and injects run details (parameters, blocks, logger).
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global CLIENT, LOGGER

        # Initialize global Client and Logger instances only if not already done
        if not CLIENT:
            run_id = os.environ.get('ORCH_RUN_ID')
            token = os.environ.get('ORCH_TOKEN')
            api_base = os.environ.get('ORCH_API_BASE_URL')
            
            if not all([run_id, token, api_base]):
                raise EnvironmentError("Flow cannot run. Orchestration environment variables are missing.")
            
            # Use lazy import to prevent circular dependency issues
            from .client import OrchestratorClient
            CLIENT = OrchestratorClient(run_id, token, api_base)
            LOGGER = OrchestratorLogger(CLIENT)

        # --- Execution starts here ---
        
        try:
            # Re-fetch details. The client handles the status update to RUNNING 
            # within the execute_lastcron_flow, but we fetch details here for safety 
            # and to get the latest parameters/blocks.
            details = CLIENT.get_run_details()
            if not details:
                raise RuntimeError("Failed to fetch run details for execution.")
            
            # Prepare arguments to pass to the user's function
            # The user's function must accept 'parameters', 'blocks', and 'logger'.
            flow_kwargs: Dict[str, Any] = {
                'parameters': details.get('parameters', {}),
                'blocks': details.get('blocks', []), 
                'logger': LOGGER
            }
            
            # Call the user's function
            func(**flow_kwargs)
            
            # --- Success Callback ---
            LOGGER.log('INFO', "Flow finished execution successfully.")
            CLIENT.update_status('COMPLETED', exit_code=0)

        except Exception as e:
            # --- Failure Callback ---
            error_message = f"Flow execution failed. Error: {e}\n{traceback.format_exc()}"
            LOGGER.log('ERROR', error_message)
            CLIENT.update_status('FAILED', message=f"Execution error: {e}", exit_code=1)
            sys.exit(1) # Ensure the external process exits with an error code
            
    return wrapper