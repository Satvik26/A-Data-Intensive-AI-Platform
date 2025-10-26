"""
Adapters for external services.

Provides clients and connection management for:
- PostgreSQL (via SQLAlchemy)
- Redis (caching and session store)
- Kafka (event streaming)
- MinIO/S3 (object storage)

All adapters implement retry logic, circuit breakers, and proper
connection pooling following DDIA reliability patterns.
"""

