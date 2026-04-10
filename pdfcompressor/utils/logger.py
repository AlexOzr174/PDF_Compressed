"""
Logger setup with modern Python 3.14+ features
Supports file and console output with colored logs
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Final


# Log format constants
LOG_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
)
DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

# Colored log formats for console
CONSOLE_COLORS: Final[dict[str, str]] = {
    "DEBUG": "\033[36m",      # Cyan
    "INFO": "\033[32m",       # Green
    "WARNING": "\033[33m",    # Yellow
    "ERROR": "\033[31m",      # Red
    "CRITICAL": "\033[35m",   # Magenta
    "RESET": "\033[0m",       # Reset
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Save original levelname
        levelname = record.levelname
        
        # Add color if running in terminal
        if sys.stdout.isatty() and levelname in CONSOLE_COLORS:
            record.levelname = f"{CONSOLE_COLORS[levelname]}{levelname}{CONSOLE_COLORS['RESET']}"
        
        # Format the record
        formatted = super().format(record)
        
        # Restore original levelname
        record.levelname = levelname
        
        return formatted


def setup_logger(
    name: str = "pdfcompressor",
    level: int = logging.INFO,
    log_file: Path | str | None = None,
    console_output: bool = True,
    file_output: bool = True,
) -> logging.Logger:
    """
    Setup application logger with console and file handlers
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Path to log file (default: ~/.pdfcompressor/app.log)
        console_output: Enable console output
        file_output: Enable file output
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = ColoredFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if file_output:
        if log_file is None:
            log_dir = Path.home() / ".pdfcompressor" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"app_{timestamp}.log"
        else:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str = "pdfcompressor") -> logging.Logger:
    """
    Get existing logger or create default one
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If no handlers, setup default
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


# Module-level default logger
default_logger: logging.Logger = setup_logger()


def debug(msg: str, *args, **kwargs) -> None:
    """Log debug message using default logger"""
    default_logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    """Log info message using default logger"""
    default_logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    """Log warning message using default logger"""
    default_logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs) -> None:
    """Log error message using default logger"""
    default_logger.error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs) -> None:
    """Log critical message using default logger"""
    default_logger.critical(msg, *args, **kwargs)
