"""Logging configuration for the chatbot backend."""

import logging
import os
from typing import Optional


def setup_logging(level: Optional[str] = None) -> None:
    """Set up logging configuration."""
    log_level = level or os.getenv("LOG_LEVEL") or "INFO"

    # Configure logging format
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    # Set third-party library log levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.DEBUG)  # Enable debug for thinking content debugging

    logger = logging.getLogger(__name__)
    logger.info("Logging configured at level: %s", log_level)
