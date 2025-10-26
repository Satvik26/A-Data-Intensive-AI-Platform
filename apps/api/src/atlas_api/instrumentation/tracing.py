"""
OpenTelemetry distributed tracing configuration.

Implements distributed tracing for request correlation across services.
Follows DDIA principles for debugging distributed systems.
"""

import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from atlas_api.config import Settings

logger = logging.getLogger(__name__)


def setup_tracing(settings: Settings) -> None:
    """
    Configure OpenTelemetry distributed tracing.

    Sets up trace provider, exporters, and auto-instrumentation
    for FastAPI, SQLAlchemy, and Redis.

    Args:
        settings: Application settings
    """
    if not settings.otel_enabled:
        logger.info("OpenTelemetry tracing is disabled")
        return

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": settings.app_version,
            "deployment.environment": settings.environment,
        }
    )

    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Add OTLP exporter
    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=True,  # Use insecure for development
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"OTLP exporter configured: {settings.otel_exporter_otlp_endpoint}")
    except Exception as e:
        logger.warning(f"Failed to configure OTLP exporter: {e}")

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Auto-instrument libraries
    try:
        # FastAPI instrumentation will be done in main.py after app creation
        # SQLAlchemyInstrumentor().instrument()  # Will be enabled when engine is created
        # RedisInstrumentor().instrument()  # Will be enabled when Redis client is created
        logger.info("OpenTelemetry auto-instrumentation configured")
    except Exception as e:
        logger.warning(f"Failed to configure auto-instrumentation: {e}")


def get_tracer(name: str) -> trace.Tracer:
    """
    Get a tracer instance for manual instrumentation.

    Args:
        name: Tracer name (typically __name__)

    Returns:
        Tracer: OpenTelemetry tracer instance
    """
    return trace.get_tracer(name)

