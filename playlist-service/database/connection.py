from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config import settings  # aquí lees settings.db_url y settings.debug


# Declarative Base para los modelos
class Base(DeclarativeBase):
    pass


# Motor asincrónico con configuración de pool
engine = create_async_engine(
    settings.db_url,
    pool_size=10,  # número mínimo de conexiones vivas
    max_overflow=20,  # conexiones extra si el pool está lleno
    pool_timeout=30,  # segundos a esperar antes de lanzar TimeoutError
    pool_recycle=1800,  # reciclar conexiones cada 30 min (1800s)
)


# Factory de sesiones asincrónicas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Dependencia para FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
