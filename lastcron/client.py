# lastcron/client.py

import importlib
import os
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Union

from lastcron.api_client import APIClient
from lastcron.logger import OrchestratorLogger


class OrchestratorClient:
    """
    High-level client for flow execution within the orchestrator.
    Wraps the APIClient with run-specific context.
    """

    def __init__(self, run_id: str, token: str, base_url: str):
        """
        Initialize the orchestrator client.

        Args:
            run_id: The current run ID
            token: Run authentication token
            base_url: Base URL for the orchestrator API
        """
        self.run_id = run_id
        self.api = APIClient(token, base_url)
        self._workspace_id: Optional[int] = None

    def get_run_details(self) -> Optional[Dict[str, Any]]:
        """
        Fetches flow entrypoint, parameters, and blocks for the current run.

        Returns:
            Dictionary with run details or None on error
        """
        details = self.api.get_run_details(self.run_id)

        # Cache workspace_id for later use
        if details and "workspace_id" in details:
            self._workspace_id = details["workspace_id"]

        return details

    def update_status(
        self, state: str, message: Optional[str] = None, exit_code: Optional[int] = None
    ):
        """
        Updates the flow state (RUNNING, COMPLETED, FAILED).

        Args:
            state: New state
            message: Optional status message
            exit_code: Optional exit code
        """
        self.api.update_run_status(self.run_id, state, message, exit_code)

    def send_log_entry(self, log_entry: Dict[str, Any]):
        """
        Sends a single log entry.

        Args:
            log_entry: Log entry data
        """
        self.api.send_log_entry(self.run_id, log_entry)

    @property
    def workspace_id(self) -> Optional[int]:
        """
        Gets the workspace ID for the current run.
        Fetches run details if not already cached.

        Returns:
            Workspace ID or None
        """
        if self._workspace_id is None:
            self.get_run_details()
        return self._workspace_id

    def trigger_flow_by_name(
        self,
        flow_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        scheduled_start: Optional[Union[str, datetime]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Triggers another flow in the same workspace by name.

        Args:
            flow_name: The name of the flow to trigger
            parameters: Optional parameters dictionary
            scheduled_start: Optional datetime or ISO string for scheduling

        Returns:
            Created flow run details or None on error

        Raises:
            ValueError: If flow not found or validation fails
            RuntimeError: If workspace ID cannot be determined
        """
        workspace_id = self.workspace_id

        if workspace_id is None:
            raise RuntimeError("Cannot determine workspace ID for current run")

        return self.api.trigger_flow_by_name(
            workspace_id, flow_name, parameters=parameters, scheduled_start=scheduled_start
        )


# --- Main Execution Function ---


def execute_lastcron_flow(run_id: str, token: str, api_base_url: str):
    """
    Main entry point called by the orchestrator_wrapper.py.
    It bootstraps the execution environment.
    """
    client = OrchestratorClient(run_id, token, api_base_url)
    logger = OrchestratorLogger(client)

    try:
        # --- 1. Initial Status Update ---
        client.update_status("RUNNING")
        logger.log("INFO", f"LastCron execution started for Run ID: {run_id}.")

        # --- 2. Fetch Details ---
        details = client.get_run_details()
        if not details:
            raise RuntimeError("Could not retrieve run details from API.")

        entrypoint = details["flow_entrypoint"]

        # --- 3. Execute the Decorated Flow ---

        # Dynamically import the entrypoint function defined by the user
        module_path, func_name = entrypoint.split(":")

        # Correctly import the module from the user's repository structure
        # (e.g., 'src/pipeline.py' becomes 'src.pipeline')
        module_path = module_path.replace("/", ".").replace(".py", "")

        # Temporarily add the repository path to Python's path so imports work
        repo_root = os.getcwd()
        sys.path.insert(0, repo_root)

        # The imported module will contain the function decorated with @flow
        module = importlib.import_module(module_path)
        flow_function = getattr(module, func_name)

        # Since the flow function is decorated with @flow, calling it will
        # trigger all orchestration logic (status updates, block passing, etc.).
        flow_function()

    except Exception as e:
        error_details = (
            f"Execution failed during bootstrap or pre-run phase: {e}\n{traceback.format_exc()}"
        )
        logger.log("ERROR", error_details)
        client.update_status("FAILED", message=f"Bootstrap/Pre-run error: {e}", exit_code=1)
        sys.exit(1)
    finally:
        # Clean up path change
        if "repo_root" in locals():
            sys.path.pop(0)


def main():
    """
    CLI entry point for the LastCron SDK.

    This function is called when running: python -m lastcron
    It replaces the need for orchestrator_wrapper.py in each repository.

    The Laravel backend should call: python -m lastcron
    instead of: python orchestrator_wrapper.py
    """
    # The PHP FlowExecutor sets these environment variables:
    # ORCH_RUN_ID, ORCH_TOKEN, ORCH_API_BASE_URL
    run_id = os.environ.get("ORCH_RUN_ID")
    token = os.environ.get("ORCH_TOKEN")
    api_base_url = os.environ.get("ORCH_API_BASE_URL")

    if not all([run_id, token, api_base_url]):
        # This scenario means the PHP launch failed to set critical environment variables
        print("Fatal: Missing LastCron orchestration environment variables.", file=sys.stderr)
        print("Required: ORCH_RUN_ID, ORCH_TOKEN, ORCH_API_BASE_URL", file=sys.stderr)
        sys.exit(128)

    try:
        # Delegate all orchestration logic to the SDK
        execute_lastcron_flow(run_id, token, api_base_url)

    except Exception as e:
        # If the SDK failed to initialize or execute, log the error here.
        # The SDK should have already attempted an API callback, but this is a final fallback.
        print(f"FATAL LastCron Execution Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
