from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import settings  # settings.db_url y settings.debug


# Declarative Base para los modelos
class Base(DeclarativeBase):
    pass


# Motor asincrónico con configuración segura para asyncpg + pgbouncer
engine = create_async_engine(
    settings.db_url,
    pool_recycle=1800,  # reciclar conexiones cada 30 min
    pool_pre_ping=True,  # valida conexiones antes de usarlas
    connect_args={"statement_cache_size": 0},  # 🔹 importante con PgBouncer
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
        yield session
