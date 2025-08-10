"""
Test suite for logging configuration functionality.
These tests verify proper logging setup, formatters, and handlers.
"""

import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import structlog

from app.logging_config import (
    LogConfig,
    configure_logging,
    get_logger,
    setup_log_rotation,
    get_log_level,
    JSONFormatter,
)


class TestLogConfig:
    """Test the LogConfig model and configuration."""

    def test_log_config_defaults(self):
        """Test LogConfig model with default values."""
        config = LogConfig()
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.log_dir == Path("logs")
        assert config.max_bytes == 10485760  # 10MB
        assert config.backup_count == 5
        assert config.enable_console == True
        assert config.enable_file == True

    def test_log_config_custom_values(self):
        """Test LogConfig with custom values."""
        config = LogConfig(
            level="DEBUG",
            format="text",
            log_dir=Path("/custom/logs"),
            max_bytes=5242880,  # 5MB
            backup_count=3,
        )
        assert config.level == "DEBUG"
        assert config.format == "text"
        assert config.log_dir == Path("/custom/logs")

    def test_log_config_validation(self):
        """Test LogConfig validation for invalid values."""
        with pytest.raises(ValueError):
            LogConfig(level="INVALID")
        
        with pytest.raises(ValueError):
            LogConfig(format="invalid_format")
        
        with pytest.raises(ValueError):
            LogConfig(max_bytes=-1)


class TestLoggingConfiguration:
    """Test logging configuration and setup."""

    def test_configure_logging_creates_log_directory(self, tmp_path):
        """Test that configure_logging creates the log directory."""
        log_dir = tmp_path / "test_logs"
        config = LogConfig(log_dir=log_dir)
        
        configure_logging(config)
        
        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_configure_logging_json_format(self, tmp_path):
        """Test JSON formatted logging configuration."""
        config = LogConfig(
            format="json",
            log_dir=tmp_path / "logs",
            enable_file=True
        )
        
        logger = configure_logging(config)
        
        # Test JSON output
        with patch("sys.stdout") as mock_stdout:
            logger.info("test message", extra={"key": "value"})
            
            # Verify JSON format
            output = mock_stdout.write.call_args[0][0]
            parsed = json.loads(output)
            assert parsed["message"] == "test message"
            assert parsed["key"] == "value"
            assert "timestamp" in parsed

    def test_configure_logging_text_format(self, tmp_path):
        """Test text formatted logging configuration."""
        config = LogConfig(
            format="text",
            log_dir=tmp_path / "logs"
        )
        
        logger = configure_logging(config)
        
        with patch("sys.stdout") as mock_stdout:
            logger.info("test message")
            
            output = mock_stdout.write.call_args[0][0]
            assert "test message" in output
            assert "INFO" in output

    def test_get_log_level_from_environment(self):
        """Test getting log level from environment variables."""
        with patch.dict("os.environ", {"LOG_LEVEL": "DEBUG"}):
            assert get_log_level() == "DEBUG"
        
        with patch.dict("os.environ", {"LOG_LEVEL": "WARNING"}):
            assert get_log_level() == "WARNING"
        
        with patch.dict("os.environ", {}):
            assert get_log_level() == "INFO"  # Default

    def test_get_logger_returns_configured_logger(self):
        """Test get_logger returns properly configured logger."""
        logger = get_logger("test_component")
        
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")

    def test_log_rotation_setup(self, tmp_path):
        """Test log rotation configuration."""
        log_file = tmp_path / "logs" / "app.log"
        
        handler = setup_log_rotation(
            log_file=log_file,
            max_bytes=1024,  # 1KB for testing
            backup_count=2
        )
        
        assert handler is not None
        assert handler.maxBytes == 1024
        assert handler.backupCount == 2

    def test_multiple_loggers_with_different_names(self):
        """Test creating multiple loggers with different component names."""
        logger1 = get_logger("component1")
        logger2 = get_logger("component2")
        
        assert logger1 != logger2
        # Both should log with their component name
        with patch("sys.stdout") as mock_stdout:
            logger1.info("msg1")
            logger2.info("msg2")
            
            calls = mock_stdout.write.call_args_list
            assert any("component1" in str(call) for call in calls)
            assert any("component2" in str(call) for call in calls)


class TestJSONFormatter:
    """Test custom JSON formatter."""

    def test_json_formatter_basic(self):
        """Test JSON formatter with basic log record."""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test"
        assert "timestamp" in parsed

    def test_json_formatter_with_extra_fields(self):
        """Test JSON formatter with extra fields."""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.user_id = "123"
        record.request_id = "abc-def"
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["user_id"] == "123"
        assert parsed["request_id"] == "abc-def"

    def test_json_formatter_with_exception(self):
        """Test JSON formatter with exception info."""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info()
            )
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["message"] == "Error occurred"
        assert "exception" in parsed
        assert "ValueError: Test error" in parsed["exception"]


class TestStructlogIntegration:
    """Test structlog integration for structured logging."""

    def test_structlog_configuration(self):
        """Test structlog is properly configured."""
        from app.logging_config import configure_structlog
        
        configure_structlog()
        
        logger = structlog.get_logger()
        assert logger is not None
        
        # Test structured logging
        with patch("sys.stdout") as mock_stdout:
            logger.info("test", key1="value1", key2=42)
            
            output = mock_stdout.write.call_args[0][0]
            parsed = json.loads(output)
            assert parsed["event"] == "test"
            assert parsed["key1"] == "value1"
            assert parsed["key2"] == 42

    def test_structlog_context_binding(self):
        """Test structlog context variable binding."""
        from app.logging_config import configure_structlog
        
        configure_structlog()
        
        logger = structlog.get_logger()
        logger = logger.bind(request_id="123", user="test_user")
        
        with patch("sys.stdout") as mock_stdout:
            logger.info("action performed")
            
            output = mock_stdout.write.call_args[0][0]
            parsed = json.loads(output)
            assert parsed["request_id"] == "123"
            assert parsed["user"] == "test_user"