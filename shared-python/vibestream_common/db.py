"""Factory de conexión a base de datos compartida (SQLAlchemy async).

Cada servicio llama a make_engine_and_session(settings.db_url, **overrides)
con sus propios valores de pool si difieren del default, y usa el get_db()
resultante como dependencia de FastAPI.
"""

from typing import AsyncGenerator, Callable, Tuple

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def make_engine_and_session(
    db_url: str,
    *,
    pool_size: int = 5,
    max_overflow: int = 5,
    pool_timeout: int = 30,
    pool_recycle: int = 1800,
    pool_pre_ping: bool = True,
    echo: bool = False,
    **extra_engine_kwargs,
) -> Tuple[AsyncEngine, Callable[[], AsyncSession]]:
    """Crea un engine async y su session factory con la configuración de
    pool estándar del proyecto. Los servicios que necesiten tuning propio
    (p. ej. PgBouncer vía connect_args) pasan sus overrides."""
    engine = create_async_engine(
        db_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=pool_pre_ping,
        echo=echo,
        **extra_engine_kwargs,
    )

    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    return engine, session_factory


def make_get_db(
    session_factory: Callable[[], AsyncSession],
) -> Callable[[], AsyncGenerator[AsyncSession, None]]:
    """Construye la dependencia get_db() de FastAPI a partir de una
    session factory ya creada."""

    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    return get_db
