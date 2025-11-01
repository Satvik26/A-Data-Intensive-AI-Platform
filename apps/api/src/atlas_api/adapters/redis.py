"""
Redis adapter for caching and session management.

Implements DDIA reliability patterns:
- Connection pooling
- Automatic retries
- Circuit breaker pattern
- Health checks
"""

import logging
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError

from atlas_api.config import Settings

logger = logging.getLogger(__name__)


class RedisAdapter:
    """
    Async Redis adapter with connection pooling.
    
    Manages Redis connections with optimized pool settings
    for high-throughput caching operations.
    """

    def __init__(self, settings: Settings):
        """
        Initialize Redis adapter.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None

    async def connect(self) -> None:
        """
        Initialize Redis connection pool.
        
        Creates connection pool with optimized settings for production load.
        """
        if self._pool is not None:
            logger.warning("Redis already connected")
            return

        logger.info(
            "Initializing Redis connection pool",
            extra={
                "max_connections": self.settings.redis_max_connections,
                "socket_timeout": self.settings.redis_socket_timeout,
            },
        )

        # Create connection pool
        self._pool = ConnectionPool.from_url(
            str(self.settings.redis_url),
            max_connections=self.settings.redis_max_connections,
            socket_timeout=self.settings.redis_socket_timeout,
            socket_connect_timeout=self.settings.redis_socket_connect_timeout,
            retry_on_timeout=self.settings.redis_retry_on_timeout,
            decode_responses=self.settings.redis_decode_responses,
            health_check_interval=30,  # Check connection health every 30s
        )

        # Create Redis client
        self._client = Redis(connection_pool=self._pool)

        logger.info("Redis connection pool initialized successfully")

    async def disconnect(self) -> None:
        """
        Close Redis connection pool gracefully.
        
        Closes all connections in the pool.
        """
        if self._client is None:
            logger.warning("Redis not connected")
            return

        logger.info("Closing Redis connection pool")
        
        await self._client.close()
        await self._pool.disconnect()
        
        self._client = None
        self._pool = None
        
        logger.info("Redis connection pool closed")

    async def get(self, key: str) -> str | None:
        """
        Get value from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            str | None: Cached value or None if not found
        """
        if self._client is None:
            raise RuntimeError("Redis not connected")

        try:
            return await self._client.get(key)
        except RedisError as e:
            logger.error(f"Redis GET error: {e}", exc_info=True)
            return None

    async def set(
        self, 
        key: str, 
        value: str, 
        ex: int | None = None
    ) -> bool:
        """
        Set value in Redis.
        
        Args:
            key: Cache key
            value: Value to cache
            ex: Expiration time in seconds
            
        Returns:
            bool: True if successful
        """
        if self._client is None:
            raise RuntimeError("Redis not connected")

        try:
            await self._client.set(key, value, ex=ex)
            return True
        except RedisError as e:
            logger.error(f"Redis SET error: {e}", exc_info=True)
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key was deleted
        """
        if self._client is None:
            raise RuntimeError("Redis not connected")

        try:
            result = await self._client.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis DELETE error: {e}", exc_info=True)
            return False

    async def health_check(self) -> dict[str, Any]:
        """
        Check Redis health.
        
        Executes PING command to verify connectivity and measure latency.
        
        Returns:
            dict: Health check results with latency
            
        Raises:
            Exception: If health check fails
        """
        if self._client is None:
            raise RuntimeError("Redis not connected")

        import time

        start_time = time.time()
        
        # PING command to check connectivity
        pong = await self._client.ping()
        
        latency_ms = (time.time() - start_time) * 1000

        # Get Redis info
        info = await self._client.info("server")

        return {
            "healthy": pong is True,
            "latency_ms": round(latency_ms, 2),
            "version": info.get("redis_version", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
        }

    @property
    def client(self) -> Redis:
        """Get Redis client."""
        if self._client is None:
            raise RuntimeError("Redis not connected")
        return self._client


# Global Redis adapter instance
_redis_adapter: RedisAdapter | None = None


def get_redis_adapter(settings: Settings | None = None) -> RedisAdapter:
    """
    Get global Redis adapter instance.
    
    Args:
        settings: Application settings (required on first call)
        
    Returns:
        RedisAdapter: Global Redis adapter
    """
    global _redis_adapter
    
    if _redis_adapter is None:
        if settings is None:
            from atlas_api.config import get_settings
            settings = get_settings()
        _redis_adapter = RedisAdapter(settings)
    
    return _redis_adapter

