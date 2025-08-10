"""Logging configuration for the Digital Garden application."""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class LogConfig(BaseModel):
    """Configuration for application logging."""

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="json", description="Log format: 'json' or 'text'")
    log_dir: Path = Field(default=Path("logs"), description="Directory for log files")
    max_bytes: int = Field(default=10485760, description="Max size per log file (10MB)")
    backup_count: int = Field(default=5, description="Number of backup files to keep")

    class Config:
        """Pydantic config."""

        use_enum_values = True


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields
        if hasattr(record, "correlation_id"):
            log_obj["correlation_id"] = record.correlation_id
        if hasattr(record, "method"):
            log_obj["method"] = record.method
        if hasattr(record, "path"):
            log_obj["path"] = record.path
        if hasattr(record, "status_code"):
            log_obj["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging(config: Optional[LogConfig] = None) -> None:
    """
    Set up application logging with the given configuration.

    Args:
        config: LogConfig instance or None for defaults
    """
    if config is None:
        config = LogConfig()

    # Create logs directory if it doesn't exist
    config.log_dir.mkdir(parents=True, exist_ok=True)

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.level))

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        config.log_dir / "app.log",
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
    )
    file_handler.setLevel(getattr(logging, config.level))

    # Set formatters
    if config.format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Set specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
