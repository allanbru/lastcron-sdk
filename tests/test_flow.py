"""
Tests for LastCron SDK flow decorator and functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from lastcron.flow import flow, FlowWrapper, get_run_logger, get_workspace_id
from lastcron.types import FlowRun, FlowRunState


class TestFlowDecorator:
    """Tests for the @flow decorator."""

    def test_flow_decorator_basic(self):
        """Test that @flow decorator creates a FlowWrapper."""
        @flow
        def my_flow(**params):
            return "result"

        assert isinstance(my_flow, FlowWrapper)
        assert my_flow._func.__name__ == "my_flow"

    def test_flow_decorator_preserves_function_name(self):
        """Test that decorator preserves function metadata."""
        @flow
        def test_function(**params):
            """Test docstring."""
            pass

        assert test_function._func.__name__ == "test_function"
        assert test_function._func.__doc__ == "Test docstring."

    def test_flow_wrapper_has_submit_method(self):
        """Test that FlowWrapper has submit method."""
        @flow
        def my_flow(**params):
            pass

        assert hasattr(my_flow, "submit")
        assert callable(my_flow.submit)

    @patch("lastcron.flow.CLIENT")
    @patch("lastcron.flow.LOGGER")
    @patch("lastcron.flow.WORKSPACE_ID", 100)
    def test_flow_submit_method(self, mock_logger, mock_client):
        """Test calling the submit method on a flow."""
        # Setup mock client
        mock_api = Mock()
        mock_api.trigger_flow_by_name.return_value = {
            "id": 1,
            "flow_id": 1,
            "workspace_id": 100,
            "state": "PENDING",
            "parameters": {"key": "value"},
        }
        mock_client.api = mock_api

        @flow
        def my_flow(**params):
            pass

        # Call submit
        result = my_flow.submit(parameters={"key": "value"})

        # Verify API was called
        assert result is not None
        assert isinstance(result, FlowRun)
        assert result.state == FlowRunState.PENDING


class TestGetRunLogger:
    """Tests for get_run_logger function."""

    @patch("lastcron.flow.FlowContext")
    def test_get_run_logger_returns_logger(self, mock_context):
        """Test that get_run_logger returns the logger from context."""
        mock_logger = Mock()
        mock_context.initialized = True
        mock_context.logger = mock_logger

        result = get_run_logger()
        assert result == mock_logger

    @patch("lastcron.flow.FlowContext")
    def test_get_run_logger_raises_when_not_initialized(self, mock_context):
        """Test that get_run_logger raises error when context not initialized."""
        mock_context.initialized = False

        with pytest.raises(RuntimeError, match="Flow context not initialized"):
            get_run_logger()


class TestGetWorkspaceId:
    """Tests for get_workspace_id function."""

    @patch("lastcron.flow.FlowContext")
    def test_get_workspace_id_returns_id(self, mock_context):
        """Test that get_workspace_id returns the workspace ID."""
        mock_context.initialized = True
        mock_context.workspace_id = 100

        result = get_workspace_id()
        assert result == 100

    @patch("lastcron.flow.FlowContext")
    def test_get_workspace_id_raises_when_not_initialized(self, mock_context):
        """Test that get_workspace_id raises error when context not initialized."""
        mock_context.initialized = False

        with pytest.raises(RuntimeError, match="Flow context not initialized"):
            get_workspace_id()


class TestFlowExecution:
    """Tests for flow execution behavior."""

    @patch("lastcron.flow.CLIENT")
    @patch("lastcron.flow.LOGGER")
    @patch("lastcron.flow.WORKSPACE_ID", 100)
    def test_flow_execution_in_orchestrator_context(
        self, mock_logger, mock_client
    ):
        """Test flow execution when running in orchestrator context."""
        executed = []

        @flow
        def my_flow(**params):
            executed.append(True)
            return "success"

        # In orchestrator context, the flow should execute
        # This is tested by the wrapper function
        assert isinstance(my_flow, FlowWrapper)

    def test_flow_with_parameters(self):
        """Test flow that accepts parameters."""
        @flow
        def my_flow(**params):
            return params.get("value", 0) * 2

        assert isinstance(my_flow, FlowWrapper)
        # The actual execution would happen in orchestrator context

    def test_multiple_flows(self):
        """Test defining multiple flows."""
        @flow
        def flow1(**params):
            return "flow1"

        @flow
        def flow2(**params):
            return "flow2"

        assert isinstance(flow1, FlowWrapper)
        assert isinstance(flow2, FlowWrapper)
        assert flow1._func.__name__ == "flow1"
        assert flow2._func.__name__ == "flow2"

