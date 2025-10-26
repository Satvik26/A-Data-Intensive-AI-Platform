"""
Configuration management for Atlas API.

Uses Pydantic Settings for type-safe configuration with environment variable support.
All settings are validated at startup to fail fast on misconfiguration.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings have sensible defaults for development and can be overridden
    via environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    environment: Literal["development", "staging", "production", "test"] = Field(
        default="development",
        description="Application environment",
    )
    app_name: str = Field(default="atlas-api", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    secret_key: str = Field(
        default="dev-secret-key-change-in-production-min-32-chars",
        description="Secret key for signing tokens",
        min_length=32,
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API port")
    api_workers: int = Field(default=4, ge=1, description="Number of worker processes")
    api_reload: bool = Field(default=False, description="Auto-reload on code changes")
    api_prefix: str = Field(default="/api/v1", description="API route prefix")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS",
    )

    # Database - PostgreSQL
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://atlas:atlas_dev@localhost:5432/atlas_dev",
        description="PostgreSQL connection URL",
    )
    database_pool_size: int = Field(
        default=20,
        ge=1,
        description="Database connection pool size",
    )
    database_max_overflow: int = Field(
        default=10,
        ge=0,
        description="Max overflow connections",
    )
    database_pool_timeout: int = Field(
        default=30,
        ge=1,
        description="Pool timeout in seconds",
    )
    database_pool_recycle: int = Field(
        default=3600,
        ge=1,
        description="Connection recycle time in seconds",
    )
    database_echo: bool = Field(
        default=False,
        description="Echo SQL statements",
    )

    # Redis
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_max_connections: int = Field(
        default=50,
        ge=1,
        description="Redis max connections",
    )
    redis_socket_timeout: int = Field(
        default=5,
        ge=1,
        description="Redis socket timeout",
    )
    redis_socket_connect_timeout: int = Field(
        default=5,
        ge=1,
        description="Redis connect timeout",
    )
    redis_retry_on_timeout: bool = Field(
        default=True,
        description="Retry on timeout",
    )
    redis_decode_responses: bool = Field(
        default=True,
        description="Decode responses to strings",
    )

    # Kafka
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers",
    )
    kafka_client_id: str = Field(
        default="atlas-api",
        description="Kafka client ID",
    )
    kafka_group_id: str = Field(
        default="atlas-api-group",
        description="Kafka consumer group ID",
    )
    kafka_auto_offset_reset: Literal["earliest", "latest"] = Field(
        default="earliest",
        description="Auto offset reset strategy",
    )
    kafka_enable_auto_commit: bool = Field(
        default=False,
        description="Enable auto commit (prefer manual for reliability)",
    )
    kafka_max_poll_records: int = Field(
        default=500,
        ge=1,
        description="Max records per poll",
    )
    kafka_session_timeout_ms: int = Field(
        default=30000,
        ge=1000,
        description="Session timeout in ms",
    )
    kafka_request_timeout_ms: int = Field(
        default=40000,
        ge=1000,
        description="Request timeout in ms",
    )

    # MinIO / S3
    minio_endpoint: str = Field(
        default="localhost:9000",
        description="MinIO endpoint",
    )
    minio_access_key: str = Field(
        default="minioadmin",
        description="MinIO access key",
    )
    minio_secret_key: str = Field(
        default="minioadmin",
        description="MinIO secret key",
    )
    minio_secure: bool = Field(default=False, description="Use HTTPS for MinIO")
    minio_region: str = Field(default="us-east-1", description="MinIO region")
    minio_bucket_name: str = Field(
        default="atlas-data",
        description="Default bucket name",
    )

    # Observability - Prometheus
    prometheus_enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics",
    )
    metrics_namespace: str = Field(
        default="atlas",
        description="Metrics namespace",
    )
    metrics_subsystem: str = Field(
        default="api",
        description="Metrics subsystem",
    )

    # Observability - OpenTelemetry
    otel_enabled: bool = Field(
        default=True,
        description="Enable OpenTelemetry",
    )
    otel_service_name: str = Field(
        default="atlas-api",
        description="Service name for traces",
    )
    otel_exporter_otlp_endpoint: str = Field(
        default="http://localhost:4317",
        description="OTLP exporter endpoint",
    )

    # Reliability - Retry Configuration
    retry_max_attempts: int = Field(
        default=3,
        ge=1,
        description="Max retry attempts",
    )
    retry_multiplier: int = Field(
        default=2,
        ge=1,
        description="Exponential backoff multiplier",
    )
    retry_min_wait: int = Field(
        default=1,
        ge=0,
        description="Min wait between retries (seconds)",
    )
    retry_max_wait: int = Field(
        default=10,
        ge=1,
        description="Max wait between retries (seconds)",
    )
    retry_jitter: bool = Field(
        default=True,
        description="Add jitter to retry delays",
    )

    # Reliability - Circuit Breaker
    circuit_breaker_failure_threshold: int = Field(
        default=5,
        ge=1,
        description="Failures before opening circuit",
    )
    circuit_breaker_recovery_timeout: int = Field(
        default=60,
        ge=1,
        description="Seconds before attempting recovery",
    )

    # Reliability - Timeouts (seconds)
    http_timeout: int = Field(default=30, ge=1, description="HTTP request timeout")
    database_timeout: int = Field(default=10, ge=1, description="Database query timeout")
    redis_timeout: int = Field(default=5, ge=1, description="Redis operation timeout")
    kafka_timeout: int = Field(default=30, ge=1, description="Kafka operation timeout")

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
    )
    rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        description="Requests per minute",
    )
    rate_limit_burst: int = Field(
        default=10,
        ge=1,
        description="Burst allowance",
    )

    # Feature Flags
    feature_ml_serving: bool = Field(
        default=True,
        description="Enable ML serving features",
    )
    feature_async_processing: bool = Field(
        default=True,
        description="Enable async processing",
    )
    feature_caching: bool = Field(
        default=True,
        description="Enable caching",
    )
    feature_outbox_pattern: bool = Field(
        default=True,
        description="Enable outbox pattern for events",
    )

    # Pagination
    default_page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Default page size",
    )
    max_page_size: int = Field(
        default=100,
        ge=1,
        description="Maximum page size",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses asyncpg driver."""
        if isinstance(v, str) and "postgresql://" in v and "asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.environment == "test"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses LRU cache to ensure settings are loaded only once.
    This is the recommended way to access settings throughout the application.

    Returns:
        Settings: Application settings instance
    """
    return Settings()

