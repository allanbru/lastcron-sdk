"""
Pytest configuration and shared fixtures for LastCron SDK tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
from lastcron.api_client import APIClient
from lastcron.logger import OrchestratorLogger
from lastcron.client import OrchestratorClient


@pytest.fixture
def mock_api_client():
    """Create a mock API client for testing."""
    client = Mock(spec=APIClient)
    client.base_url = "https://api.example.com"
    client.token = "test-token"
    return client


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock(spec=OrchestratorLogger)
    return logger


@pytest.fixture
def mock_orchestrator_client():
    """Create a mock orchestrator client for testing."""
    client = Mock(spec=OrchestratorClient)
    client.run_id = "test-run-123"
    client.api = Mock(spec=APIClient)
    client.logger = Mock(spec=OrchestratorLogger)
    return client


@pytest.fixture
def sample_block_data():
    """Sample block data for testing."""
    return {
        "id": 1,
        "workspace_id": 100,
        "key_name": "test-block",
        "type": "STRING",
        "value": "test-value",
        "is_secret": False,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_flow_data():
    """Sample flow data for testing."""
    return {
        "id": 1,
        "workspace_id": 100,
        "name": "test-flow",
        "description": "Test flow description",
        "file_path": "flows/test_flow.py",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_flow_run_data():
    """Sample flow run data for testing."""
    return {
        "id": 1,
        "flow_id": 1,
        "workspace_id": 100,
        "state": "COMPLETED",
        "parameters": {"key": "value"},
        "scheduled_start": "2024-01-01T00:00:00Z",
        "started_at": "2024-01-01T00:00:00Z",
        "completed_at": "2024-01-01T00:00:01Z",
        "exit_code": 0,
        "message": "Success",
    }


@pytest.fixture
def sample_workspace_data():
    """Sample workspace data for testing."""
    return {
        "id": 100,
        "name": "Test Workspace",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

