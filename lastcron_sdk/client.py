# lastcron_sdk/client.py

import requests
import sys
import importlib
import os
import traceback
from typing import Dict, Any, Optional
from .logger import OrchestratorLogger

class OrchestratorClient:
    """Handles low-level API communication with the Laravel orchestrator."""

    def __init__(self, run_id: str, token: str, base_url: str):
        self.run_id = run_id
        self.base_url = base_url.rstrip('/')
        self.headers = {"Authorization": f"Bearer {token}"}

    def _call(self, method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None):
        """Internal method to execute authenticated HTTP requests."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, json=json_data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Log failure to stderr, but allow execution to continue unless critical
            print(f"API Communication Error to {endpoint}: {e}", file=sys.stderr)
            return None

    def get_run_details(self) -> Optional[Dict[str, Any]]:
        """Fetches flow entrypoint, parameters, and blocks."""
        return self._call('GET', f"runs/{self.run_id}")

    def update_status(self, state: str, message: str = None, exit_code: int = None):
        """Updates the flow state (RUNNING, COMPLETED, FAILED)."""
        data = {'state': state, 'message': message, 'exit_code': exit_code}
        self._call('POST', f"runs/{self.run_id}/status", json_data=data)
    
    def send_log_entry(self, log_entry: Dict[str, Any]):
        """Sends a single log entry."""
        self._call('POST', f"runs/{self.run_id}/logs", json_data=log_entry)

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
        client.update_status('RUNNING')
        logger.log('INFO', f"LastCron execution started for Run ID: {run_id}.")
        
        # --- 2. Fetch Details ---
        details = client.get_run_details()
        if not details:
            raise RuntimeError("Could not retrieve run details from API.")

        entrypoint = details['flow_entrypoint']
        
        # --- 3. Execute the Decorated Flow ---
        
        # Dynamically import the entrypoint function defined by the user
        module_path, func_name = entrypoint.split(':')
        
        # Correctly import the module from the user's repository structure
        # (e.g., 'src/pipeline.py' becomes 'src.pipeline')
        module_path = module_path.replace('/', '.').replace('.py', '')
        
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
        error_details = f"Execution failed during bootstrap or pre-run phase: {e}\n{traceback.format_exc()}"
        logger.log('ERROR', error_details)
        client.update_status('FAILED', message=f"Bootstrap/Pre-run error: {e}", exit_code=1)
        sys.exit(1)
    finally:
        # Clean up path change
        if 'repo_root' in locals():
            sys.path.pop(0)