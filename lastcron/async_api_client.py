# lastcron/async_api_client.py

import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import aiohttp

from lastcron.utils import validate_and_format_timestamp, validate_flow_name, validate_parameters


class AsyncAPIClient:
    """
    Asynchronous API client for LastCron orchestrator.
    Provides high-level async wrappers for all API operations.
    """

    def __init__(self, token: str, base_url: str):
        """
        Initialize the async API client.

        Args:
            token: Authentication token (run token or user token)
            base_url: Base URL for the API (e.g., http://localhost/api)
        """
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"}
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Context manager entry."""
        self._session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._session:
            await self._session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Internal method to execute async HTTP requests with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json_data: JSON body data
            params: URL query parameters

        Returns:
            Response JSON or None on error
        """
        if not self._session:
            self._session = aiohttp.ClientSession(headers=self.headers)

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            async with self._session.request(
                method, url, json=json_data, params=params, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"API Error [{method} {endpoint}]: {e}", file=sys.stderr)
            return None

    # --- Orchestrator API Endpoints ---

    async def get_run_details(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches flow run details including entrypoint, parameters, and blocks.

        Args:
            run_id: The run ID

        Returns:
            Dictionary with run details or None on error
        """
        return await self._request("GET", f"orchestrator/runs/{run_id}")

    async def update_run_status(
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

        return await self._request("POST", f"orchestrator/runs/{run_id}/status", json_data=data)

    async def send_log_entry(
        self, run_id: str, log_entry: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Sends a log entry for a run.

        Args:
            run_id: The run ID
            log_entry: Log entry data (log_time, level, message)

        Returns:
            Response data or None on error
        """
        return await self._request("POST", f"orchestrator/runs/{run_id}/logs", json_data=log_entry)

    # --- V1 API Endpoints ---

    async def list_workspace_flows(self, workspace_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Lists all flows in a workspace.

        Args:
            workspace_id: The workspace ID

        Returns:
            List of flow dictionaries or None on error
        """
        return await self._request("GET", f"v1/workspaces/{workspace_id}/flows")  # type: ignore[return-value]

    async def get_flow_by_name(self, workspace_id: int, flow_name: str) -> Optional[Dict[str, Any]]:
        """
        Finds a flow by name in a workspace.

        Args:
            workspace_id: The workspace ID
            flow_name: The flow name to search for

        Returns:
            Flow dictionary or None if not found
        """
        flow_name = validate_flow_name(flow_name)
        flows = await self.list_workspace_flows(workspace_id)

        if not flows:
            return None

        for flow in flows:
            if flow.get("name") == flow_name:
                return flow

        return None

    async def trigger_flow_by_id(
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

        return await self._request("POST", f"v1/flows/{flow_id}/trigger", json_data=data)

    async def trigger_flow_by_name(
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
        flow = await self.get_flow_by_name(workspace_id, flow_name)

        if not flow:
            raise ValueError(f"Flow '{flow_name}' not found in workspace {workspace_id}")

        # Trigger by ID
        return await self.trigger_flow_by_id(
            flow["id"], parameters=parameters, scheduled_start=scheduled_start
        )

    async def get_flow_runs(
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

        return await self._request("GET", f"v1/flows/{flow_id}/runs", params=params)  # type: ignore[return-value]

    async def get_run_logs(self, run_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Gets logs for a specific run.

        Args:
            run_id: The run ID

        Returns:
            List of log entries or None on error
        """
        return await self._request("GET", f"v1/runs/{run_id}/logs")  # type: ignore[return-value]

    async def close(self):
        """Close the session explicitly."""
        if self._session:
            await self._session.close()
            self._session = None
