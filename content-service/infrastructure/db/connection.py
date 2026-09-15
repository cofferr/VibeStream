from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import settings


# content-service/database/connection.py
engine = create_async_engine(
    settings.db_url,
    echo=False,  # 🔴 NUNCA True en producción
    pool_size=5,           # 🔥 REDUCIDO
    max_overflow=5,        # 🔥 REDUCIDO  
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    # ✅ Configuración CORRECTA para PgBouncer
    connect_args={
        "statement_cache_size": 100,  # ✅ Cache pequeño pero funcional
        "prepared_statement_cache_size": 100,  # ✅ Cache pequeño
        "server_settings": {
            "jit": "off"  # ✅ Mejor rendimiento con PgBouncer
        }
    },
)


# Factory de sesiones asincrónicas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


# Dependency para FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
