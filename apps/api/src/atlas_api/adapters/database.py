"""
Database adapter for PostgreSQL with async connection pooling.

Implements DDIA reliability patterns:
- Connection pooling with proper sizing
- Graceful connection management
- Health checks and monitoring
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from atlas_api.config import Settings

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    """
    Async database adapter with connection pooling.
    
    Manages database connections using SQLAlchemy async engine
    with optimized pool settings for high concurrency.
    """

    def __init__(self, settings: Settings):
        """
        Initialize database adapter.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        """
        Initialize database connection pool.
        
        Creates async engine with optimized pool settings for production load.
        """
        if self._engine is not None:
            logger.warning("Database already connected")
            return

        logger.info(
            "Initializing database connection pool",
            extra={
                "pool_size": self.settings.database_pool_size,
                "max_overflow": self.settings.database_max_overflow,
                "pool_timeout": self.settings.database_pool_timeout,
            },
        )

        # Create async engine with connection pooling
        # Note: Async engines use AsyncAdaptedQueuePool by default, no need to specify poolclass
        self._engine = create_async_engine(
            str(self.settings.database_url),
            # Connection pool settings
            pool_size=self.settings.database_pool_size,
            max_overflow=self.settings.database_max_overflow,
            pool_timeout=self.settings.database_pool_timeout,
            pool_recycle=self.settings.database_pool_recycle,
            pool_pre_ping=True,  # Verify connections before using
            # Performance settings
            echo=self.settings.database_echo,
            echo_pool=False,
            # Async settings
            future=True,
        )

        # Create session factory
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("Database connection pool initialized successfully")

    async def disconnect(self) -> None:
        """
        Close database connection pool gracefully.
        
        Disposes of all connections in the pool.
        """
        if self._engine is None:
            logger.warning("Database not connected")
            return

        logger.info("Closing database connection pool")
        
        await self._engine.dispose()
        self._engine = None
        self._session_factory = None
        
        logger.info("Database connection pool closed")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session from pool.
        
        Yields:
            AsyncSession: Database session
            
        Raises:
            RuntimeError: If database not connected
        """
        if self._session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def health_check(self) -> dict[str, any]:
        """
        Check database health.
        
        Executes a simple query to verify database connectivity
        and measure latency.
        
        Returns:
            dict: Health check results with latency and pool stats
            
        Raises:
            Exception: If health check fails
        """
        if self._engine is None:
            raise RuntimeError("Database not connected")

        import time
        from sqlalchemy import text

        start_time = time.time()
        
        async with self._engine.connect() as conn:
            # Simple query to check connectivity
            result = await conn.execute(text("SELECT 1 as health_check"))
            row = result.fetchone()
            
        latency_ms = (time.time() - start_time) * 1000

        # Get pool statistics
        pool = self._engine.pool
        pool_stats = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.size() + pool.overflow(),
        }

        return {
            "healthy": row[0] == 1,
            "latency_ms": round(latency_ms, 2),
            "pool": pool_stats,
        }

    @property
    def engine(self) -> AsyncEngine:
        """Get database engine."""
        if self._engine is None:
            raise RuntimeError("Database not connected")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get session factory."""
        if self._session_factory is None:
            raise RuntimeError("Database not connected")
        return self._session_factory


# Global database adapter instance
_db_adapter: DatabaseAdapter | None = None


def get_database_adapter(settings: Settings | None = None) -> DatabaseAdapter:
    """
    Get global database adapter instance.
    
    Args:
        settings: Application settings (required on first call)
        
    Returns:
        DatabaseAdapter: Global database adapter
    """
    global _db_adapter
    
    if _db_adapter is None:
        if settings is None:
            from atlas_api.config import get_settings
            settings = get_settings()
        _db_adapter = DatabaseAdapter(settings)
    
    return _db_adapter


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    Yields:
        AsyncSession: Database session
    """
    db = get_database_adapter()
    async for session in db.get_session():
        yield session

