# lastcron_sdk/flow.py

import functools
import sys
import os
import atexit
from typing import Any, Optional, Dict, List
import traceback
from lastcron_sdk.logger import OrchestratorLogger
from lastcron_sdk.client import OrchestratorClient
from lastcron_sdk.types import Parameters, FlowRun, FlowFunction, Timestamp, Block

# Global instances will be set by the wrapper
CLIENT: Optional[OrchestratorClient] = None
LOGGER: Optional[OrchestratorLogger] = None
WORKSPACE_ID: Optional[int] = None

# Track registered flows for auto-execution
_REGISTERED_FLOWS: List['FlowWrapper'] = []
_AUTO_EXECUTE_SETUP = False

class FlowContext:
    initialized = False
    parameters: Parameters
    blocks: List[Dict[str, Any]]
    logger: OrchestratorLogger
    workspace_id: int

    def __init__(
        self,
        parameters: Parameters,
        blocks: Dict[str, Any],
        logger: OrchestratorLogger,
        workspace_id: int
    ):
        self.initialized = True
        self.parameters = parameters
        self.blocks = blocks
        self.logger = logger
        self.workspace_id = workspace_id

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlowContext':
        return cls(
            parameters=data.get('parameters', {}),
            blocks=data.get('blocks', []),
            logger=LOGGER,
            workspace_id=data.get('workspace_id')
        )


class FlowWrapper:
    """
    Wrapper class for flow functions that adds the .submit() method.

    This allows flows to be triggered programmatically like:
        example_flow.submit(parameters={'key': 'value'}, scheduled_start=datetime.now())
    """

    def __init__(self, func: FlowFunction, flow_name: str):
        """
        Initialize the flow wrapper.

        Args:
            func: The decorated flow function
            flow_name: Name of the flow (function name)
        """
        self._func = func
        self._flow_name = flow_name
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        """Call the wrapped function normally."""
        return self._func(*args, **kwargs)

    def submit(
        self,
        parameters: Optional[Parameters] = None,
        scheduled_start: Optional[Timestamp] = None,
        **kwargs
    ) -> Optional[FlowRun]:
        """
        Submit this flow for execution.

        This method allows you to trigger the flow programmatically from within
        another flow or from external code.

        Args:
            parameters: Optional parameters to pass to the flow
            scheduled_start: Optional datetime or ISO string for scheduling
            **kwargs: Additional keyword arguments (reserved for future use)

        Returns:
            FlowRun dataclass with the created run details, or None on error

        Example:
            >>> @flow
            >>> def my_flow(logger, workspace_id, **params):
            >>>     logger.info("Flow running")
            >>>
            >>> # Trigger the flow from another flow
            >>> run = my_flow.submit(parameters={'key': 'value'})
            >>> if run:
            >>>     print(f"Triggered run ID: {run.id}")

        Raises:
            RuntimeError: If called outside of a flow context
        """
        global CLIENT, WORKSPACE_ID

        if not CLIENT:
            raise RuntimeError(
                f"{self._flow_name}.submit() can only be called from within a flow execution context. "
                "Ensure you're calling this from within a @flow decorated function."
            )

        if WORKSPACE_ID is None:
            raise RuntimeError(
                "Workspace ID not available in flow context. "
                "This should not happen - please check the flow initialization."
            )

        # Use the API client to trigger the flow
        result = CLIENT.api.trigger_flow_by_name(
            workspace_id=WORKSPACE_ID,
            flow_name=self._flow_name,
            parameters=parameters,
            scheduled_start=scheduled_start
        )

        if not result:
            return None

        # Convert to FlowRun dataclass
        return FlowRun.from_dict(result)

def flow(func: FlowFunction) -> FlowWrapper:
    """
    The core LastCron decorator.
    It wraps the user's primary function, manages the run lifecycle,
    and injects run details (parameters, blocks, logger).

    Returns a FlowWrapper that adds the .submit() method to the flow function.

    Example:
        >>> @flow
        >>> def my_flow(logger, workspace_id, **params):
        >>>     logger.info("Flow running")
        >>>
        >>> # Can be called normally when executed by orchestrator
        >>> my_flow()
        >>>
        >>> # Or triggered programmatically from another flow
        >>> run = my_flow.submit(parameters={'key': 'value'})
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global CLIENT, LOGGER, WORKSPACE_ID

        # Initialize global Client and Logger instances only if not already done
        if not CLIENT:
            run_id = os.environ.get('ORCH_RUN_ID')
            token = os.environ.get('ORCH_TOKEN')
            api_base = os.environ.get('ORCH_API_BASE_URL')

            if not all([run_id, token, api_base]):
                raise EnvironmentError("Flow cannot run. Orchestration environment variables are missing.")

            # Use lazy import to prevent circular dependency issues
            from lastcron_sdk.client import OrchestratorClient
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

            # Store workspace_id globally for use by run_flow()
            WORKSPACE_ID = details.get('workspace_id')

            # Prepare arguments to pass to the user's function
            # The user's function must accept 'parameters', 'blocks', 'logger', and 'workspace_id'.
            flow_kwargs: Dict[str, Any] = {
                'parameters': details.get('parameters', {}),
                'blocks': details.get('blocks', []),
                'logger': LOGGER,
                'workspace_id': WORKSPACE_ID
            }

            if FlowContext.initialized:
                # TODO: if we're calling another run, we should trigger it via API
                raise RuntimeError("Flow context already initialized. Ensure the flow decorator is used only once.")

            FlowContext.from_dict(details)

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

    # Return a FlowWrapper that adds the .submit() method
    flow_wrapper = FlowWrapper(wrapper, func.__name__)

    # Register this flow for potential auto-execution
    _REGISTERED_FLOWS.append(flow_wrapper)
    _setup_auto_execution()

    return flow_wrapper


def _setup_auto_execution():
    """
    Sets up auto-execution of flows when the script is run directly.

    This function is called when a flow is decorated. It checks if:
    1. The script is being run as __main__ (python flow_file.py)
    2. Orchestration environment variables are present

    If both conditions are met, it registers an atexit handler to execute
    the flow automatically when the module finishes loading.
    """
    global _AUTO_EXECUTE_SETUP

    # Only set up once
    if _AUTO_EXECUTE_SETUP:
        return

    _AUTO_EXECUTE_SETUP = True

    # Check if we have orchestration environment variables
    run_id = os.environ.get('ORCH_RUN_ID')
    token = os.environ.get('ORCH_TOKEN')
    api_base = os.environ.get('ORCH_API_BASE_URL')

    # If environment variables are present, set up auto-execution
    if all([run_id, token, api_base]):
        # Register the execution to happen after the module is fully loaded
        # This ensures all flows are decorated before we try to execute
        atexit.register(_auto_execute_flow)


def _auto_execute_flow():
    """
    Automatically executes the flow if the script is run directly.

    This is called via atexit after the module finishes loading.
    It finds the flow to execute and runs it.
    """
    # Check if this is the main module being executed
    import __main__
    if not hasattr(__main__, '__file__'):
        return

    main_file = os.path.abspath(__main__.__file__)

    # Find flows defined in the main file
    flows_to_execute = []
    for flow_wrapper in _REGISTERED_FLOWS:
        # Get the module where the flow was defined
        flow_module = flow_wrapper._func.__module__

        # If the flow is in __main__, it's in the file being executed
        if flow_module == '__main__':
            flows_to_execute.append(flow_wrapper)

    # Execute the first flow found (typically there's only one per file)
    if flows_to_execute:
        flow_to_run = flows_to_execute[0]

        if len(flows_to_execute) > 1:
            # If multiple flows, warn but still execute the first one
            print(f"Warning: Multiple flows found in {main_file}. Executing: {flow_to_run._flow_name}",
                  file=sys.stderr)

        # Execute the flow
        flow_to_run()

def get_run_logger() -> OrchestratorLogger:
    """
    Returns the global logger instance for the current run.
    """
    if FlowContext.initialized:
        return FlowContext.logger

    raise RuntimeError("Flow context not initialized. Ensure the flow decorator is used.")


def get_block(key_name: str) -> Optional[Block]:
    """
    Retrieves a configuration block by key name.

    This function fetches blocks on-demand from the API, allowing flows
    to retrieve only the configuration they need instead of loading all
    blocks upfront.

    Args:
        key_name: The block's key name (e.g., 'aws-credentials', 'api-key')

    Returns:
        Block dataclass with the configuration value, or None if not found

    Example:
        >>> @flow
        >>> def my_flow(logger, workspace_id, **params):
        >>>     # Get AWS credentials block
        >>>     aws_creds = get_block('aws-credentials')
        >>>     if aws_creds:
        >>>         logger.info(f"Got AWS credentials: {aws_creds.value}")
        >>>
        >>>     # Get API key block
        >>>     api_key = get_block('api-key')
        >>>     if api_key and api_key.is_secret:
        >>>         logger.info("API key is encrypted")

    Raises:
        RuntimeError: If called outside of a flow context
    """
    global CLIENT

    if not CLIENT:
        raise RuntimeError(
            "get_block() can only be called from within a flow execution context. "
            "Ensure you're calling this from within a @flow decorated function."
        )

    # Get the run_id from the client
    run_id = CLIENT.run_id

    # Fetch the block from the API
    return CLIENT.api.get_block(run_id, key_name)

def run_flow(
    flow_name: str,
    parameters: Optional[Parameters] = None,
    scheduled_start: Optional[Timestamp] = None
) -> Optional[FlowRun]:
    """
    Triggers another flow in the same workspace by name.

    This function allows you to programmatically trigger other flows from within
    a running flow. The triggered flow will execute asynchronously.

    The workspace_id is automatically determined from the current flow context,
    so you don't need to pass it manually.

    Args:
        flow_name: The name of the flow to trigger (must be in the same workspace)
        parameters: Optional dictionary of parameters to pass to the triggered flow
        scheduled_start: Optional datetime or ISO format string for when to start the flow.
                        If None, the flow starts immediately.

    Returns:
        FlowRun dataclass containing the created flow run details including:
        - id: The run ID
        - flow_id: The ID of the triggered flow
        - state: Initial state (typically 'PENDING')
        - parameters: The parameters passed to the run
        - scheduled_start: When the run is scheduled to start

        Returns None if the trigger request failed.

    Example:
        >>> # Trigger a flow immediately with parameters
        >>> run = run_flow('data_processing', parameters={'batch_size': 100})
        >>> if run:
        >>>     print(f"Triggered flow run ID: {run['id']}")

        >>> # Schedule a flow for later
        >>> from datetime import datetime, timedelta
        >>> future_time = datetime.now() + timedelta(hours=1)
        >>> run = run_flow('cleanup_job', scheduled_start=future_time)

    Raises:
        RuntimeError: If called outside of a flow context (not within a @flow decorated function)
        ValueError: If flow not found, timestamp invalid, or parameters invalid
        TypeError: If parameters are not a dictionary
    """
    global CLIENT, LOGGER, WORKSPACE_ID

    if not CLIENT:
        raise RuntimeError(
            "run_flow() can only be called from within a flow execution context. "
            "Ensure you're calling this from within a @flow decorated function."
        )

    if WORKSPACE_ID is None:
        raise RuntimeError(
            "Workspace ID not available in flow context. "
            "This should not happen - please check the flow initialization."
        )

    # Log the trigger attempt
    LOGGER.info(f"Triggering flow '{flow_name}' in workspace {WORKSPACE_ID}")

    try:
        # Use the API client directly with the workspace_id from context
        result = CLIENT.api.trigger_flow_by_name(
            workspace_id=WORKSPACE_ID,
            flow_name=flow_name,
            parameters=parameters,
            scheduled_start=scheduled_start
        )

        if result:
            # Convert to FlowRun dataclass
            flow_run = FlowRun.from_dict(result)
            LOGGER.info(
                f"Successfully triggered flow '{flow_name}'. "
                f"Run ID: {flow_run.id}, State: {flow_run.state.value}"
            )
            return flow_run
        else:
            LOGGER.error(f"Failed to trigger flow '{flow_name}' - API returned None")
            return None

    except ValueError as e:
        # Flow not found or validation error
        LOGGER.error(f"Failed to trigger flow '{flow_name}': {e}")
        return None
    except TypeError as e:
        # Invalid parameter types
        LOGGER.error(f"Invalid parameters for flow '{flow_name}': {e}")
        return None
    except Exception as e:
        # Unexpected error
        LOGGER.error(f"Unexpected error triggering flow '{flow_name}': {e}")
        return None

