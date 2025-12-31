"""
Centralized debug logging for ANM V0-OpenSource.

This module provides a rotating file logger for debug information,
replacing the 50+ hardcoded absolute paths throughout the codebase.
"""

import os
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


class DebugLogger:
    """
    Centralized debug logger with automatic log rotation.

    Features:
    - Configurable log path via environment variable
    - Automatic log rotation (10MB max per file, keeps 5 backup files)
    - Thread-safe logging
    - JSON-formatted debug messages
    - Graceful fallback if logging fails
    """

    _instance: Optional['DebugLogger'] = None
    _logger: Optional[logging.Logger] = None

    def __init__(self):
        """Initialize the debug logger with rotation."""
        # Get log path from environment or use default
        log_path = os.getenv(
            "ANM_DEBUG_LOG",
            os.path.join(".anm_cache", "debug.log")
        )

        # Ensure directory exists
        log_dir = os.path.dirname(log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # Create logger
        self._logger = logging.getLogger("ANM_Debug")
        self._logger.setLevel(logging.DEBUG)

        # Remove existing handlers to avoid duplicates
        self._logger.handlers.clear()

        # Create rotating file handler
        # Max 10MB per file, keep 5 backup files
        try:
            handler = RotatingFileHandler(
                log_path,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )

            # Set format
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)

            self._logger.addHandler(handler)
            self._logger.info(f"Debug logger initialized: {log_path}")

        except Exception as e:
            # Fallback to console if file logging fails
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
            self._logger.warning(f"Could not create log file {log_path}: {e}")

    @classmethod
    def get_instance(cls) -> 'DebugLogger':
        """Get singleton instance of debug logger."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def log_dict(self, data: Dict[str, Any], level: str = "DEBUG") -> None:
        """
        Log a dictionary as JSON.

        Args:
            data: Dictionary to log
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        try:
            json_str = json.dumps(data, indent=2, default=str)
            log_method = getattr(self._logger, level.lower(), self._logger.debug)
            log_method(json_str)
        except Exception as e:
            # Never let logging break the application
            self._logger.error(f"Failed to log dictionary: {e}")

    def log(self, message: str, level: str = "DEBUG", **kwargs) -> None:
        """
        Log a message with optional context.

        Args:
            message: Log message
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            **kwargs: Additional context to include in log
        """
        try:
            if kwargs:
                context = json.dumps(kwargs, default=str)
                full_message = f"{message} | Context: {context}"
            else:
                full_message = message

            log_method = getattr(self._logger, level.lower(), self._logger.debug)
            log_method(full_message)
        except Exception as e:
            # Never let logging break the application
            self._logger.error(f"Failed to log message: {e}")

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.log(message, "DEBUG", **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.log(message, "INFO", **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.log(message, "WARNING", **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.log(message, "ERROR", **kwargs)


# Global singleton instance
_debug_logger_instance = None


def get_debug_logger() -> DebugLogger:
    """
    Get the global debug logger instance.

    This function is the recommended way to access the debug logger
    throughout the ANM codebase.

    Returns:
        DebugLogger instance
    """
    global _debug_logger_instance
    if _debug_logger_instance is None:
        _debug_logger_instance = DebugLogger.get_instance()
    return _debug_logger_instance


def log_debug(data: Any, **context) -> None:
    """
    Quick debug logging function.

    Args:
        data: Data to log (dict, string, or any JSON-serializable object)
        **context: Additional context key-value pairs
    """
    try:
        logger = get_debug_logger()

        if isinstance(data, dict):
            if context:
                data = {**data, **context}
            logger.log_dict(data)
        elif isinstance(data, str):
            logger.debug(data, **context)
        else:
            # Convert to dict
            logger.log_dict({
                "data": str(data),
                **context
            })
    except Exception:
        # Never let debug logging break the application
        pass


# Convenience function for backward compatibility
def write_debug_log(data: Dict[str, Any]) -> None:
    """
    Write debug log entry (backward compatibility).

    This function mimics the old behavior of writing JSON to debug.log
    but uses the new centralized logger with rotation.

    Args:
        data: Dictionary to log
    """
    try:
        logger = get_debug_logger()
        logger.log_dict(data)
    except Exception:
        # Silent failure - debug logging should never break the app
        pass
