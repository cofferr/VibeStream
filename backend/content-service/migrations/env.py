import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Fase 6: content-service gestiona con Alembic solo las tablas que
# realmente escribe (albums, songs, genres, song_artists) — ver
# infrastructure/db/models.py. No incluye artists (artist-service es su
# dueño) ni ninguna otra tabla ajena.
from config import settings
from infrastructure.db.models import Base

config = context.config

# settings.db_url es la misma fuente de verdad que usa la app (Fase 6):
# evita duplicar la URL de conexión en alembic.ini.
config.set_main_option("sqlalchemy.url", settings.db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    # alembic_version se deja en el schema "public" (default) a propósito:
    # si viviera en "music_streaming", Alembic necesitaría que ese schema
    # ya existiera para poder crear su propia tabla de control, antes de
    # correr la migración que lo crea (huevo y gallina). "public" siempre
    # existe en un Postgres nuevo.
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
