"""
Structured logging configuration.

Implements structured JSON logging with correlation IDs for distributed tracing.
Follows DDIA Chapter 1 principles for observability and debugging.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from atlas_api.config import Settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application context to log events.

    Args:
        logger: Logger instance
        method_name: Method name being called
        event_dict: Event dictionary

    Returns:
        EventDict: Enhanced event dictionary
    """
    event_dict["app"] = "atlas-api"
    return event_dict


def setup_logging(settings: Settings) -> None:
    """
    Configure structured logging for the application.

    Sets up structlog with JSON formatting for production and
    human-readable formatting for development.

    Args:
        settings: Application settings
    """
    # Determine log level
    log_level = getattr(logging, settings.log_level.upper())

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Shared processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_app_context,
    ]

    # Environment-specific processors
    if settings.is_production or settings.environment == "staging":
        # JSON formatting for production (machine-readable)
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Console formatting for development (human-readable)
        processors = shared_processors + [
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aiokafka").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        BoundLogger: Configured logger instance
    """
    return structlog.get_logger(name)

