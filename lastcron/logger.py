# lastcron/logger.py

import datetime
import sys
from typing import TYPE_CHECKING, List, Literal, Optional

if TYPE_CHECKING:
    # Prevents circular imports and provides type hints
    from lastcron.client import OrchestratorClient


class OrchestratorLogger:
    """
    Manages logging, sending entries to the Laravel API.

    Automatically redacts secret values from log messages to prevent
    accidental exposure of sensitive information.
    """

    def __init__(self, client: "OrchestratorClient", secrets: Optional[List[str]] = None):
        """
        Initialize the logger.

        Args:
            client: The orchestrator client for sending logs
            secrets: Optional list of secret values to redact from logs
        """
        self.client = client
        self.secrets = secrets or []

    def add_secret(self, secret: str):
        """
        Add a secret value to be redacted from logs.

        Args:
            secret: The secret value to redact
        """
        if secret and secret not in self.secrets:
            self.secrets.append(str(secret))

    def add_secrets(self, secrets: List[str]):
        """
        Add multiple secret values to be redacted from logs.

        Args:
            secrets: List of secret values to redact
        """
        for secret in secrets:
            self.add_secret(str(secret))

    def _redact_secrets(self, message: str) -> str:
        """
        Redact all secret values from a message.

        Args:
            message: The original message

        Returns:
            Message with all secrets replaced by '****'
        """
        redacted = message
        for secret in self.secrets:
            if secret:  # Only redact non-empty secrets
                redacted = redacted.replace(secret, "****")
        return redacted

    def log(self, level: Literal["INFO", "WARNING", "ERROR"], message: str):
        """
        Formats and sends a single log entry via the API client.

        Automatically redacts any secret values from the message before
        logging to prevent accidental exposure.

        Args:
            level: Log level (INFO, WARNING, or ERROR)
            message: The message to log (will be redacted)
        """
        # Redact secrets from the message
        redacted_message = self._redact_secrets(str(message))

        timestamp = datetime.datetime.now().isoformat()

        # Log to stdout/stderr locally as a fallback (with redaction)
        log_line = f"[{timestamp}][{level}] {redacted_message}"
        print(log_line, file=sys.stderr if level == "ERROR" else sys.stdout)

        log_entry = {
            "log_time": timestamp,
            "level": level,
            "message": redacted_message,  # Send redacted message to API
        }

        # Send to the API asynchronously if possible, or synchronously as a fallback
        self.client.send_log_entry(log_entry)

    def info(self, message: str):
        """Logs an informational message."""
        self.log("INFO", message)

    def warning(self, message: str):
        """Logs a warning message."""
        self.log("WARNING", message)

    def error(self, message: str):
        """Logs an error message."""
        self.log("ERROR", message)
