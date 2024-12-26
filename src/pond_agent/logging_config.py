import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    logs_dir: Optional[Path] = None,
) -> None:
    """
    Set up logging configuration with both console and file handlers.

    Args:
        console_level: Logging level for console output (default: INFO)
        file_level: Logging level for file output (default: DEBUG)
        logs_dir: Directory for log files (default: project_root/logs)
    """
    # Create logs directory if it doesn't exist
    if logs_dir is None:
        # Find the project root directory (where src is located)
        current_dir = Path.cwd()
        logs_dir = current_dir / "logs"

    logs_dir.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels

    # Remove any existing handlers
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, console_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler - daily rotating
    log_file = logs_dir / f"{datetime.now():%Y%m%d}.log"
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, file_level.upper()))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Create a startup log entry
    root_logger.info("=" * 80)
    root_logger.info(f"Logging initialized: console={console_level}, file={file_level}")
    root_logger.info(f"Log file: {log_file}")
    root_logger.info("=" * 80)
