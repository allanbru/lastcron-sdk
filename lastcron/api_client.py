# lastcron/api_client.py

import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests

from lastcron.types import APIResponse, Block
from lastcron.utils import validate_and_format_timestamp, validate_flow_name, validate_parameters


class APIClient:
    """
    Synchronous API client for LastCron orchestrator.
    Provides high-level wrappers for all API operations.
    """

    def __init__(self, token: str, base_url: str):
        """
        Initialize the API client.

        Args:
            token: Authentication token (run token or user token)
            base_url: Base URL for the API (e.g., http://localhost/api)
        """
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"}

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Internal method to execute HTTP requests with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json_data: JSON body data
            params: URL query parameters

        Returns:
            Response JSON or None on error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = requests.request(
                method, url, headers=self.headers, json=json_data, params=params, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error [{method} {endpoint}]: {e}", file=sys.stderr)
            return None

    # --- Orchestrator API Endpoints ---

    def get_run_details(self, run_id: str) -> Optional[APIResponse]:
        """
        Fetches flow run details including entrypoint, parameters, and blocks.

        Args:
            run_id: The run ID

        Returns:
            Dictionary with run details or None on error
        """
        return self._request("GET", f"orchestrator/runs/{run_id}")

    def get_block(self, run_id: str, key_name: str) -> Optional[Block]:
        """
        Fetches a specific block by key name for a run.

        This allows flows to retrieve configuration blocks on-demand
        instead of getting all blocks upfront.

        Args:
            run_id: The run ID
            key_name: The block's key name (e.g., 'aws-credentials')

        Returns:
            Block dataclass or None if not found or on error

        Example:
            >>> client = APIClient(token="...", base_url="...")
            >>> block = client.get_block(run_id="123", key_name="aws-credentials")
            >>> if block:
            >>>     print(f"AWS Key: {block.value}")
        """
        response = self._request("GET", f"orchestrator/runs/{run_id}/blocks/{key_name}")

        if not response or response.get("status") != "success":
            return None

        block_data = response.get("block")
        if not block_data:
            return None

        return Block.from_dict(block_data)

    def update_run_status(
        self,
        run_id: str,
        state: str,
        message: Optional[str] = None,
        exit_code: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Updates the flow run status.

        Args:
            run_id: The run ID
            state: New state (RUNNING, COMPLETED, FAILED)
            message: Optional status message
            exit_code: Optional exit code

        Returns:
            Response data or None on error
        """
        data: Dict[str, Any] = {"state": state}
        if message is not None:
            data["message"] = message
        if exit_code is not None:
            data["exit_code"] = exit_code

        return self._request("POST", f"orchestrator/runs/{run_id}/status", json_data=data)

    def send_log_entry(self, run_id: str, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Sends a log entry for a run.

        Args:
            run_id: The run ID
            log_entry: Log entry data (log_time, level, message)

        Returns:
            Response data or None on error
        """
        return self._request("POST", f"orchestrator/runs/{run_id}/logs", json_data=log_entry)

    # --- V1 API Endpoints (accessible via both /api/v1 and /api/orchestrator) ---

    def list_workspace_flows(self, workspace_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Lists all flows in a workspace.

        Args:
            workspace_id: The workspace ID

        Returns:
            List of flow dictionaries or None on error
        """
        # Use orchestrator endpoint when using run token (for flows triggering other flows)
        return self._request("GET", f"orchestrator/workspaces/{workspace_id}/flows")  # type: ignore[return-value]

    def get_flow_by_name(self, workspace_id: int, flow_name: str) -> Optional[Dict[str, Any]]:
        """
        Finds a flow by name in a workspace.

        Args:
            workspace_id: The workspace ID
            flow_name: The flow name to search for

        Returns:
            Flow dictionary or None if not found
        """
        flow_name = validate_flow_name(flow_name)
        flows = self.list_workspace_flows(workspace_id)

        if not flows:
            return None

        for flow in flows:
            if flow.get("name") == flow_name:
                return flow

        return None

    def trigger_flow_by_id(
        self,
        flow_id: int,
        parameters: Optional[Dict[str, Any]] = None,
        scheduled_start: Optional[Union[str, datetime]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Triggers a flow run by flow ID.

        Args:
            flow_id: The flow ID
            parameters: Optional parameters dictionary
            scheduled_start: Optional datetime or ISO string for scheduling

        Returns:
            Created flow run details or None on error

        Raises:
            ValueError: If timestamp validation fails
            TypeError: If parameters are invalid
        """
        # Validate inputs
        parameters = validate_parameters(parameters)
        scheduled_start_str = validate_and_format_timestamp(scheduled_start)

        # Build request data
        data: Dict[str, Any] = {}
        if parameters is not None:
            data["parameters"] = parameters
        if scheduled_start_str is not None:
            data["scheduled_start"] = scheduled_start_str

        # Use orchestrator endpoint when using run token (for flows triggering other flows)
        return self._request("POST", f"orchestrator/flows/{flow_id}/trigger", json_data=data)

    def trigger_flow_by_name(
        self,
        workspace_id: int,
        flow_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        scheduled_start: Optional[Union[str, datetime]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Triggers a flow run by flow name.

        Args:
            workspace_id: The workspace ID
            flow_name: The flow name
            parameters: Optional parameters dictionary
            scheduled_start: Optional datetime or ISO string for scheduling

        Returns:
            Created flow run details or None on error

        Raises:
            ValueError: If flow not found or timestamp validation fails
            TypeError: If parameters are invalid
        """
        # Find the flow by name
        flow = self.get_flow_by_name(workspace_id, flow_name)

        if not flow:
            raise ValueError(f"Flow '{flow_name}' not found in workspace {workspace_id}")

        # Trigger by ID
        return self.trigger_flow_by_id(
            flow["id"], parameters=parameters, scheduled_start=scheduled_start
        )

    def get_flow_runs(
        self, flow_id: int, limit: Optional[int] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Gets run history for a flow.

        Args:
            flow_id: The flow ID
            limit: Optional limit on number of runs to return

        Returns:
            List of run dictionaries or None on error
        """
        params = {}
        if limit is not None:
            params["limit"] = limit

        # Use orchestrator endpoint when using run token (for flows triggering other flows)
        return self._request("GET", f"orchestrator/flows/{flow_id}/runs", params=params)  # type: ignore[return-value]

    def get_run_logs(self, run_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Gets logs for a specific run.

        Args:
            run_id: The run ID

        Returns:
            List of log entries or None on error
        """
        # Use orchestrator endpoint when using run token (for flows triggering other flows)
        return self._request("GET", f"orchestrator/runs/{run_id}/logs")  # type: ignore[return-value]
