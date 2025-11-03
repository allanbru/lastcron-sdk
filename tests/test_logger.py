"""
Tests for LastCron SDK logger.
"""

import pytest
from unittest.mock import Mock, patch, call
from lastcron.logger import OrchestratorLogger
from lastcron.client import OrchestratorClient


class TestOrchestratorLogger:
    """Tests for OrchestratorLogger."""

    def test_logger_creation(self, mock_orchestrator_client):
        """Test creating a logger instance."""
        logger = OrchestratorLogger(mock_orchestrator_client)
        assert logger.client == mock_orchestrator_client
        assert logger.secrets == []

    def test_logger_with_secrets(self, mock_orchestrator_client):
        """Test creating a logger with secrets."""
        secrets = ["secret1", "secret2"]
        logger = OrchestratorLogger(mock_orchestrator_client, secrets=secrets)
        assert logger.secrets == secrets

    def test_add_secret(self, mock_orchestrator_client):
        """Test adding a secret to the logger."""
        logger = OrchestratorLogger(mock_orchestrator_client)
        logger.add_secret("my-secret")
        assert "my-secret" in logger.secrets

    def test_redact_secrets(self, mock_orchestrator_client):
        """Test that secrets are redacted from messages."""
        logger = OrchestratorLogger(mock_orchestrator_client, secrets=["secret123"])
        message = "The password is secret123 and should be hidden"
        redacted = logger._redact_secrets(message)
        assert "secret123" not in redacted
        assert "****" in redacted

    def test_redact_multiple_secrets(self, mock_orchestrator_client):
        """Test redacting multiple secrets."""
        logger = OrchestratorLogger(
            mock_orchestrator_client, secrets=["secret1", "secret2"]
        )
        message = "secret1 and secret2 should both be redacted"
        redacted = logger._redact_secrets(message)
        assert "secret1" not in redacted
        assert "secret2" not in redacted
        assert redacted.count("****") == 2

    def test_info_logging(self, mock_orchestrator_client):
        """Test info level logging."""
        logger = OrchestratorLogger(mock_orchestrator_client)
        logger.info("Test info message")

        # Logger prints to stdout, no client method calls needed

    def test_warning_logging(self, mock_orchestrator_client):
        """Test warning level logging."""
        logger = OrchestratorLogger(mock_orchestrator_client)
        logger.warning("Test warning message")

        # Logger prints to stdout

    def test_error_logging(self, mock_orchestrator_client):
        """Test error level logging."""
        logger = OrchestratorLogger(mock_orchestrator_client)
        logger.error("Test error message")

        # Logger prints to stderr

    def test_logging_with_secret_redaction(self, mock_orchestrator_client):
        """Test that secrets are redacted when logging."""
        logger = OrchestratorLogger(mock_orchestrator_client, secrets=["password123"])

        # Test that the secret is redacted
        redacted = logger._redact_secrets("The password is password123")
        assert "password123" not in redacted
        assert "****" in redacted

    def test_empty_secrets_list(self, mock_orchestrator_client):
        """Test logger with no secrets."""
        logger = OrchestratorLogger(mock_orchestrator_client)
        message = "This message has no secrets"
        redacted = logger._redact_secrets(message)
        assert redacted == message

    def test_secret_case_sensitive(self, mock_orchestrator_client):
        """Test that secret redaction is case-sensitive."""
        logger = OrchestratorLogger(mock_orchestrator_client, secrets=["Secret"])
        message = "Secret should be redacted but secret should not"
        redacted = logger._redact_secrets(message)
        assert "Secret" not in redacted
        assert "secret" in redacted  # lowercase version not redacted

