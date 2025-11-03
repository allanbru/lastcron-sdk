"""
Tests for LastCron SDK type definitions.
"""

import pytest
from datetime import datetime
from lastcron.types import (
    Block,
    BlockType,
    Flow,
    FlowRun,
    FlowRunState,
    Workspace,
)


class TestBlockType:
    """Tests for BlockType enum."""

    def test_block_type_values(self):
        """Test that BlockType has expected values."""
        assert BlockType.SECRET == "SECRET"
        assert BlockType.STRING == "STRING"
        assert BlockType.JSON == "JSON"
        assert BlockType.MARKDOWN == "MARKDOWN"


class TestFlowRunState:
    """Tests for FlowRunState enum."""

    def test_flow_run_state_values(self):
        """Test that FlowRunState has expected values."""
        assert FlowRunState.PENDING == "PENDING"
        assert FlowRunState.LAUNCHING == "LAUNCHING"
        assert FlowRunState.RUNNING == "RUNNING"
        assert FlowRunState.COMPLETED == "COMPLETED"
        assert FlowRunState.FAILED == "FAILED"


class TestBlock:
    """Tests for Block dataclass."""

    def test_block_creation(self):
        """Test creating a Block instance."""
        block = Block(
            key_name="test-block",
            type=BlockType.STRING,
            value="test-value",
            id=1,
            workspace_id=100,
        )
        assert block.key_name == "test-block"
        assert block.type == BlockType.STRING
        assert block.value == "test-value"
        assert block.id == 1
        assert block.workspace_id == 100

    def test_block_from_dict(self, sample_block_data):
        """Test creating Block from dictionary."""
        block = Block.from_dict(sample_block_data)
        assert block.id == 1
        assert block.workspace_id == 100
        assert block.key_name == "test-block"
        assert block.type == BlockType.STRING
        assert block.value == "test-value"
        assert block.is_secret is False

    def test_block_secret(self):
        """Test creating a secret Block."""
        block = Block(
            key_name="api-key",
            type=BlockType.SECRET,
            value="secret-value",
            is_secret=True,
        )
        assert block.is_secret is True
        assert block.type == BlockType.SECRET


class TestFlow:
    """Tests for Flow dataclass."""

    def test_flow_creation(self):
        """Test creating a Flow instance."""
        flow = Flow(
            id=1,
            workspace_id=100,
            name="test-flow",
            entrypoint="flows/test.py:main",
            description="Test flow",
        )
        assert flow.id == 1
        assert flow.name == "test-flow"
        assert flow.entrypoint == "flows/test.py:main"

    def test_flow_from_dict(self, sample_flow_data):
        """Test creating Flow from dictionary."""
        # Add required entrypoint field
        sample_flow_data["entrypoint"] = "flows/test_flow.py:main"
        flow = Flow.from_dict(sample_flow_data)
        assert flow.id == 1
        assert flow.workspace_id == 100
        assert flow.name == "test-flow"
        assert flow.description == "Test flow description"


class TestFlowRun:
    """Tests for FlowRun dataclass."""

    def test_flow_run_creation(self):
        """Test creating a FlowRun instance."""
        run = FlowRun(
            id=1,
            flow_id=1,
            state=FlowRunState.RUNNING,
            parameters={"key": "value"},
        )
        assert run.id == 1
        assert run.flow_id == 1
        assert run.state == FlowRunState.RUNNING
        assert run.parameters == {"key": "value"}

    def test_flow_run_from_dict(self, sample_flow_run_data):
        """Test creating FlowRun from dictionary."""
        run = FlowRun.from_dict(sample_flow_run_data)
        assert run.id == 1
        assert run.flow_id == 1
        assert run.state == FlowRunState.COMPLETED
        assert run.parameters == {"key": "value"}
        assert run.exit_code == 0
        assert run.message == "Success"

    def test_flow_run_state_enum(self):
        """Test that FlowRun properly uses FlowRunState enum."""
        run = FlowRun(
            id=1,
            flow_id=1,
            state=FlowRunState.FAILED,
        )
        assert run.state == FlowRunState.FAILED
        assert run.state.value == "FAILED"


class TestWorkspace:
    """Tests for Workspace dataclass."""

    def test_workspace_creation(self):
        """Test creating a Workspace instance."""
        workspace = Workspace(
            id=100,
            name="Test Workspace",
        )
        assert workspace.id == 100
        assert workspace.name == "Test Workspace"

    def test_workspace_from_dict(self, sample_workspace_data):
        """Test creating Workspace from dictionary."""
        workspace = Workspace.from_dict(sample_workspace_data)
        assert workspace.id == 100
        assert workspace.name == "Test Workspace"

