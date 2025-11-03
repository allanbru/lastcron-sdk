"""
Type definitions for the LastCron SDK.

This module provides strongly-typed dataclasses and type aliases
for better type safety and IDE support.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

# ============================================================================
# Enums
# ============================================================================


class BlockType(str, Enum):
    """Types of configuration blocks."""

    SECRET = "SECRET"
    STRING = "STRING"
    JSON = "JSON"
    MARKDOWN = "MARKDOWN"


class FlowRunState(str, Enum):
    """States of a flow run."""

    PENDING = "PENDING"
    LAUNCHING = "LAUNCHING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ============================================================================
# Block Types
# ============================================================================


@dataclass(frozen=True)
class Block:
    """
    Represents a configuration block.

    Blocks can contain secrets, configuration values, or other data
    that flows need to access. Secret blocks are encrypted in the database.

    Attributes:
        id: Unique identifier for the block
        workspace_id: ID of the workspace this block belongs to (None for global blocks)
        key_name: Programmatic key name (e.g., 'aws-credentials')
        type: Type of the block (SECRET, STRING, JSON, MARKDOWN)
        value: The actual value (decrypted if it was a secret)
        is_secret: Whether this block contains sensitive data
        created_at: When the block was created
        updated_at: When the block was last updated
    """

    key_name: str
    type: BlockType
    value: str
    id: Optional[int] = None
    workspace_id: Optional[int] = None
    is_secret: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        """Create a Block from a dictionary (API response)."""
        return cls(
            id=data.get("id"),
            workspace_id=data.get("workspace_id"),
            key_name=data["key_name"],
            type=BlockType(data["type"]),
            value=data["value"],
            is_secret=data.get("is_secret", False),
            created_at=cls._parse_datetime(data.get("created_at")),
            updated_at=cls._parse_datetime(data.get("updated_at")),
        )

    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from API response."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None


# ============================================================================
# Flow Types
# ============================================================================


@dataclass(frozen=True)
class Flow:
    """
    Represents a flow definition.

    Attributes:
        id: Unique identifier for the flow
        workspace_id: ID of the workspace this flow belongs to
        name: Human-readable name of the flow
        entrypoint: Path to the flow entrypoint (e.g., 'src/pipeline.py:main_flow')
        description: Optional description of what the flow does
        created_at: When the flow was created
        updated_at: When the flow was last updated
    """

    id: int
    workspace_id: int
    name: str
    entrypoint: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Flow":
        """Create a Flow from a dictionary (API response)."""
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            name=data["name"],
            entrypoint=data["entrypoint"],
            description=data.get("description"),
            created_at=Block._parse_datetime(data.get("created_at")),
            updated_at=Block._parse_datetime(data.get("updated_at")),
        )


@dataclass(frozen=True)
class FlowRun:
    """
    Represents a flow run (execution instance).

    Attributes:
        id: Unique identifier for the run
        flow_id: ID of the flow being executed
        state: Current state of the run
        parameters: Parameters passed to this run
        scheduled_start: When the run is scheduled to start
        started_at: When the run actually started
        completed_at: When the run completed
        exit_code: Exit code of the process (if completed)
        message: Status message
        created_at: When the run was created
        updated_at: When the run was last updated
    """

    id: int
    flow_id: int
    state: FlowRunState
    parameters: Dict[str, Any] = field(default_factory=dict)
    scheduled_start: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlowRun":
        """Create a FlowRun from a dictionary (API response)."""
        return cls(
            id=data["id"],
            flow_id=data["flow_id"],
            state=FlowRunState(data["state"]),
            parameters=data.get("parameters", {}),
            scheduled_start=Block._parse_datetime(data.get("scheduled_start")),
            started_at=Block._parse_datetime(data.get("started_at")),
            completed_at=Block._parse_datetime(data.get("completed_at")),
            exit_code=data.get("exit_code"),
            message=data.get("message"),
            created_at=Block._parse_datetime(data.get("created_at")),
            updated_at=Block._parse_datetime(data.get("updated_at")),
        )


# ============================================================================
# Workspace Types
# ============================================================================


@dataclass(frozen=True)
class Workspace:
    """
    Represents a workspace.

    Attributes:
        id: Unique identifier for the workspace
        name: Name of the workspace
        git_repo_url: URL of the Git repository
        git_branch: Branch to use
        created_at: When the workspace was created
        updated_at: When the workspace was last updated
    """

    id: int
    name: str
    git_repo_url: Optional[str] = None
    git_branch: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workspace":
        """Create a Workspace from a dictionary (API response)."""
        return cls(
            id=data["id"],
            name=data["name"],
            git_repo_url=data.get("git_repo_url"),
            git_branch=data.get("git_branch"),
            created_at=Block._parse_datetime(data.get("created_at")),
            updated_at=Block._parse_datetime(data.get("updated_at")),
        )


# ============================================================================
# Type Aliases
# ============================================================================

# Parameters can be any JSON-serializable dictionary
Parameters = Dict[str, Any]

# Blocks list
BlockList = List[Block]

# Timestamp can be datetime object or ISO string
Timestamp = Union[datetime, str]

# Flow function signature
FlowFunction = Callable[..., None]

# API response types
APIResponse = Dict[str, Any]
APIResponseList = List[Dict[str, Any]]


# ============================================================================
# Request/Response Types
# ============================================================================


@dataclass
class TriggerFlowRequest:
    """Request to trigger a flow."""

    flow_name: str
    parameters: Optional[Parameters] = None
    scheduled_start: Optional[Timestamp] = None


@dataclass
class TriggerFlowResponse:
    """Response from triggering a flow."""

    run: FlowRun

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriggerFlowResponse":
        """Create from API response."""
        return cls(run=FlowRun.from_dict(data))


@dataclass
class GetBlockRequest:
    """Request to get a block by name."""

    key_name: str
    workspace_id: Optional[int] = None


@dataclass
class ListBlocksResponse:
    """Response from listing blocks."""

    blocks: BlockList

    @classmethod
    def from_dict(cls, data: List[Dict[str, Any]]) -> "ListBlocksResponse":
        """Create from API response."""
        return cls(blocks=[Block.from_dict(b) for b in data])
