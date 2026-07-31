from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _ensure_async_driver(url: str) -> str:
    """Map a sync sqlite URL to its async driver for create_async_engine.

    Render-style DATABASE_URL values (e.g. "sqlite:///./app.db") omit the
    async driver; SQLAlchemy would then load the sync pysqlite dialect and
    crash at import. Rewriting the scheme keeps the engine async-compatible.
    """
    if url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
        return "sqlite+aiosqlite://" + url[len("sqlite://") :]
    return url


engine = create_async_engine(_ensure_async_driver(settings.DATABASE_URL), echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Automatically commits on success and rolls back on exception.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Create all database tables.

    Idempotent — safe to call on every startup.
    """
    import app.models.job
    import app.models.llm_cache
    import app.models.user  # noqa: F401
    from app.db.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
