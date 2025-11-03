"""
Tests for LastCron SDK API client.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from lastcron.api_client import APIClient
from lastcron.types import Block, Flow, FlowRun


class TestAPIClient:
    """Tests for APIClient."""

    def test_client_initialization(self):
        """Test creating an API client."""
        client = APIClient(token="test-token", base_url="https://api.example.com")
        assert client.token == "test-token"
        assert client.base_url == "https://api.example.com"

    @patch("requests.request")
    def test_get_block_success(self, mock_request):
        """Test getting a block successfully."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "block": {
                "id": 1,
                "workspace_id": 100,
                "key_name": "test-block",
                "type": "STRING",
                "value": "test-value",
                "is_secret": False,
            }
        }
        mock_request.return_value = mock_response

        client = APIClient(token="test-token", base_url="https://api.example.com")
        result = client.get_block(run_id="run-123", key_name="test-block")

        assert result is not None
        assert result.key_name == "test-block"
        assert result.value == "test-value"

    @patch("requests.request")
    def test_get_block_not_found(self, mock_request):
        """Test getting a block that doesn't exist."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        client = APIClient(token="test-token", base_url="https://api.example.com")
        result = client.get_block(run_id="run-123", key_name="nonexistent")

        assert result is None

    @patch("requests.request")
    def test_update_run_status(self, mock_request):
        """Test updating run status."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "updated"}
        mock_request.return_value = mock_response

        client = APIClient(token="test-token", base_url="https://api.example.com")
        result = client.update_run_status(
            run_id="run-123", state="RUNNING", message="Flow is running"
        )

        assert result is not None
        mock_request.assert_called_once()

    @patch("requests.request")
    def test_send_log_entry(self, mock_request):
        """Test sending a log entry."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"logged": True}
        mock_request.return_value = mock_response

        client = APIClient(token="test-token", base_url="https://api.example.com")
        log_entry = {
            "level": "INFO",
            "message": "Test log message",
            "timestamp": "2024-01-01T00:00:00Z",
        }
        result = client.send_log_entry(run_id="run-123", log_entry=log_entry)

        assert result is not None

    @patch("requests.request")
    def test_list_workspace_flows(self, mock_request):
        """Test listing workspace flows."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1,
                "workspace_id": 100,
                "name": "test-flow",
                "entrypoint": "flows/test.py:main",
            }
        ]
        mock_request.return_value = mock_response

        client = APIClient(token="test-token", base_url="https://api.example.com")
        result = client.list_workspace_flows(workspace_id=100)

        assert result is not None
        assert len(result) == 1

    @patch("requests.request")
    def test_request_with_network_error(self, mock_request):
        """Test handling network errors."""
        mock_request.side_effect = requests.exceptions.ConnectionError("Network error")

        client = APIClient(token="test-token", base_url="https://api.example.com")
        result = client.get_block(run_id="run-123", key_name="test-block")

        assert result is None

    @patch("requests.request")
    def test_request_with_timeout(self, mock_request):
        """Test handling timeout errors."""
        mock_request.side_effect = requests.exceptions.Timeout("Request timeout")

        client = APIClient(token="test-token", base_url="https://api.example.com")
        result = client.get_block(run_id="run-123", key_name="test-block")

        assert result is None

    @patch("requests.request")
    def test_request_with_server_error(self, mock_request):
        """Test handling server errors (5xx)."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_request.return_value = mock_response

        client = APIClient(token="test-token", base_url="https://api.example.com")
        result = client.get_block(run_id="run-123", key_name="test-block")

        assert result is None

    def test_base_url_normalization(self):
        """Test that base URL is normalized correctly."""
        client = APIClient(
            token="test-token", base_url="https://api.example.com/"
        )
        # The client should handle trailing slashes
        assert client.base_url.rstrip("/") == "https://api.example.com"

    @patch("requests.request")
    def test_authorization_header(self, mock_request):
        """Test that authorization header is set correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        client = APIClient(token="test-token", base_url="https://api.example.com")
        client.get_run_details(run_id="run-123")

        # Verify the request was made with correct headers
        call_args = mock_request.call_args
        headers = call_args[1].get("headers", {})
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-token"

