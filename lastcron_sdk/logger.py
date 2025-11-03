# lastcron_sdk/logger.py

import datetime
import sys
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    # Prevents circular imports and provides type hints
    from lastcron_sdk.client import OrchestratorClient 

class OrchestratorLogger:
    """Manages logging, sending entries to the Laravel API."""

    def __init__(self, client: 'OrchestratorClient'):
        self.client = client
        
    def log(self, level: Literal['INFO', 'WARNING', 'ERROR'], message: str):
        """Formats and sends a single log entry via the API client."""
        
        timestamp = datetime.datetime.now().isoformat()
        
        # Log to stdout/stderr locally as a fallback
        log_line = f"[{timestamp}][{level}] {message}"
        print(log_line, file=sys.stderr if level == 'ERROR' else sys.stdout)
        
        log_entry = {
            'log_time': timestamp,
            'level': level,
            'message': message,
        }
        
        # Send to the API asynchronously if possible, or synchronously as a fallback
        self.client.send_log_entry(log_entry)
        
    def info(self, message: str):
        """Logs an informational message."""
        self.log('INFO', message)
        
    def warning(self, message: str):
        """Logs a warning message."""
        self.log('WARNING', message)
        
    def error(self, message: str):
        """Logs an error message."""
        self.log('ERROR', message)