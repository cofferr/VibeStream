"""Cubre el fix de la Fase 1 en PlaylistRepository: antes, un fallo real
de BD en add_song_to_playlist/remove_song_from_playlist/
get_user_playlists/count_user_playlists se tragaba en un `except
Exception: return False/[]/0`, indistinguible de un resultado vacío
legítimo. Ahora se re-lanza como RepositoryError.

Usa SQLite en memoria (no requiere Postgres real) para los casos de
"camino feliz", y un stub de sesión que falla a propósito para los
casos de error — no queremos levantar Postgres solo para probar que un
error se propaga con el tipo correcto.
"""


import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from vibestream_common.db import Base

from database.models import Playlist
from errors import RepositoryError
from repositories.playlist_repository import PlaylistRepository


@pytest.fixture
async def session():
    # schema_translate_map: los modelos declaran __table_args__ =
    # {"schema": "music_streaming"} (Postgres); SQLite no tiene ese
    # concepto, así que se traduce a "sin schema" solo para el test.
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        execution_options={"schema_translate_map": {"music_streaming": None}},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as s:
        yield s

    await engine.dispose()


class _RaisingSession:
    """Stub de AsyncSession cuyo execute() siempre falla, para probar el
    manejo de errores sin depender de provocar un fallo real de red/BD."""

    async def execute(self, *args, **kwargs):
        raise RuntimeError("fallo simulado de infraestructura")

    async def rollback(self):
        pass


async def _make_playlist(session, user_id: int = 1, name: str = "Mi playlist") -> Playlist:
    playlist = Playlist(user_id=user_id, name=name)
    session.add(playlist)
    await session.commit()
    await session.refresh(playlist)
    return playlist


# --- camino feliz -----------------------------------------------------


async def test_add_and_get_songs(session):
    playlist = await _make_playlist(session)
    repo = PlaylistRepository(session)

    added = await repo.add_song_to_playlist(playlist.id, song_id=42, user_id=1)
    assert added is True

    rows = await repo.get_playlist_song_rows(playlist.id, user_id=1)
    assert [r.song_id for r in rows] == [42]


async def test_add_song_idempotent(session):
    """Añadir la misma canción dos veces no es un error, ya existe."""
    playlist = await _make_playlist(session)
    repo = PlaylistRepository(session)

    assert await repo.add_song_to_playlist(playlist.id, song_id=42, user_id=1) is True
    assert await repo.add_song_to_playlist(playlist.id, song_id=42, user_id=1) is True

    rows = await repo.get_playlist_song_rows(playlist.id, user_id=1)
    assert len(rows) == 1


async def test_add_song_wrong_owner_returns_false(session):
    """No es un error de infraestructura — la playlist es de otro
    usuario, así que devolver False (no encontrada) es el resultado
    legítimo, no algo que deba envolverse en RepositoryError."""
    playlist = await _make_playlist(session, user_id=1)
    repo = PlaylistRepository(session)

    result = await repo.add_song_to_playlist(playlist.id, song_id=42, user_id=999)
    assert result is False


async def test_remove_song(session):
    playlist = await _make_playlist(session)
    repo = PlaylistRepository(session)
    await repo.add_song_to_playlist(playlist.id, song_id=42, user_id=1)

    removed = await repo.remove_song_from_playlist(playlist.id, song_id=42, user_id=1)
    assert removed is True

    rows = await repo.get_playlist_song_rows(playlist.id, user_id=1)
    assert rows == []


async def test_count_and_list_user_playlists(session):
    repo = PlaylistRepository(session)
    await _make_playlist(session, name="Una")
    await _make_playlist(session, name="Otra")

    assert await repo.count_user_playlists(user_id=1) == 2
    playlists = await repo.get_user_playlists(user_id=1)
    assert {p.name for p in playlists} == {"Una", "Otra"}


# --- Fase 1: fallos reales se re-lanzan como RepositoryError, no se
# tragan como False/[]/0 -------------------------------------------------


async def test_add_song_infra_failure_raises_repository_error():
    repo = PlaylistRepository(_RaisingSession())
    with pytest.raises(RepositoryError):
        await repo.add_song_to_playlist(1, song_id=42, user_id=1)


async def test_remove_song_infra_failure_raises_repository_error():
    repo = PlaylistRepository(_RaisingSession())
    with pytest.raises(RepositoryError):
        await repo.remove_song_from_playlist(1, song_id=42, user_id=1)


async def test_get_user_playlists_infra_failure_raises_repository_error():
    repo = PlaylistRepository(_RaisingSession())
    with pytest.raises(RepositoryError):
        await repo.get_user_playlists(user_id=1)


async def test_count_user_playlists_infra_failure_raises_repository_error():
    repo = PlaylistRepository(_RaisingSession())
    with pytest.raises(RepositoryError):
        await repo.count_user_playlists(user_id=1)
