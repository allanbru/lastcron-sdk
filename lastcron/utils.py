# lastcron/utils.py

import re
from datetime import datetime, timezone
from typing import Optional, Union


def validate_and_format_timestamp(timestamp: Optional[Union[str, datetime]]) -> Optional[str]:
    """
    Validates and formats a timestamp for API submission.

    Args:
        timestamp: Can be:
            - None: Returns None (immediate execution)
            - datetime object: Converts to ISO format string
            - str: Validates ISO format and returns as-is

    Returns:
        ISO format string (YYYY-MM-DDTHH:MM:SS) or None

    Raises:
        ValueError: If timestamp is invalid or in the past

    Examples:
        >>> from datetime import datetime, timedelta
        >>> future = datetime.now() + timedelta(hours=1)
        >>> validate_and_format_timestamp(future)
        '2024-11-02T16:30:00'

        >>> validate_and_format_timestamp("2024-11-02T16:30:00")
        '2024-11-02T16:30:00'

        >>> validate_and_format_timestamp(None)
        None
    """
    if timestamp is None:
        return None

    # Handle datetime objects
    if isinstance(timestamp, datetime):
        # Get current time - use UTC if timestamp is timezone-aware, otherwise use naive
        if timestamp.tzinfo is not None:
            current_time = datetime.now(timezone.utc)
        else:
            current_time = datetime.now()

        # Check if timestamp is in the past
        if timestamp < current_time:
            raise ValueError(
                f"Scheduled start time must be in the future. "
                f"Provided: {timestamp.isoformat()}, Current: {current_time.isoformat()}"
            )
        return timestamp.isoformat()

    # Handle string timestamps
    if isinstance(timestamp, str):
        # Validate ISO format
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$"
        if not re.match(iso_pattern, timestamp):
            raise ValueError(
                f"Invalid timestamp format. Expected ISO format (YYYY-MM-DDTHH:MM:SS), "
                f"got: {timestamp}"
            )

        # Try to parse and validate it's in the future
        try:
            # Handle timezone-aware strings by removing timezone info for comparison
            timestamp_clean = timestamp.split("+")[0].split("Z")[0].split(".")[0]
            parsed = datetime.fromisoformat(timestamp_clean)

            if parsed < datetime.now():
                raise ValueError(
                    f"Scheduled start time must be in the future. "
                    f"Provided: {timestamp}, Current: {datetime.now().isoformat()}"
                )
        except ValueError as e:
            if "must be in the future" in str(e):
                raise
            raise ValueError(f"Invalid timestamp string: {timestamp}. Error: {e}") from e

        return timestamp

    # Invalid type
    raise TypeError(
        f"Timestamp must be datetime object, ISO format string, or None. "
        f"Got: {type(timestamp).__name__}"
    )


def validate_flow_name(flow_name: str) -> str:
    """
    Validates a flow name.

    Args:
        flow_name: The name of the flow

    Returns:
        The validated flow name

    Raises:
        ValueError: If flow name is invalid
    """
    if not flow_name:
        raise ValueError("Flow name cannot be empty")

    if not isinstance(flow_name, str):
        raise TypeError(f"Flow name must be a string, got: {type(flow_name).__name__}")

    if len(flow_name) > 255:
        raise ValueError(f"Flow name too long (max 255 characters): {len(flow_name)}")

    return flow_name.strip()


def validate_parameters(parameters: Optional[dict]) -> Optional[dict]:
    """
    Validates flow parameters.

    Args:
        parameters: Dictionary of parameters or None

    Returns:
        The validated parameters dictionary or None
    Raises:
        TypeError: If parameters is not a dict or None
    """
    if parameters is None:
        return None

    if not isinstance(parameters, dict):
        raise TypeError(
            f"Parameters must be a dictionary or None, got: {type(parameters).__name__}"
        )

    return parameters
