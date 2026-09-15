from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from infrastructure.db.models import Album, Song


class SongRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, song: Song) -> Song:
        self.session.add(song)
        await self.session.commit()
        await self.session.refresh(song)
        return song

    async def get_by_id(self, song_id: int) -> Song | None:
        result = await self.session.execute(select(Song).where(Song.id == song_id))
        return result.scalar_one_or_none()

    async def get_by_id_with_info(self, song_id: int) -> Song | None:
        """Obtiene una canción con álbum y artistas precargados, para
        endpoints públicos consumidos por otros servicios (playlist-service,
        search-service) que ya no tienen acceso directo a estas tablas."""
        stmt = (
            select(Song)
            .options(
                selectinload(Song.album).selectinload(Album.artist),
                selectinload(Song.artists),
            )
            .where(Song.id == song_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_ids_with_info(self, song_ids: list[int]) -> Sequence[Song]:
        """Batch de canciones por id, con álbum y artistas precargados.
        Usado por playlist-service para enriquecer su lista de song_ids
        propios en una sola llamada en vez de N."""
        if not song_ids:
            return []
        stmt = (
            select(Song)
            .options(
                selectinload(Song.album).selectinload(Album.artist),
                selectinload(Song.artists),
            )
            .where(Song.id.in_(song_ids))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_by_album(self, album_id: int) -> Sequence[Song]:
        result = await self.session.execute(
            select(Song).where(Song.album_id == album_id)
        )
        return result.scalars().all()

    async def list_by_artist(self, artist_id: int) -> Sequence[Song]:
        result = await self.session.execute(
            select(Song).join(Song.artists).where(Song.artists.any(id=artist_id))
        )
        return result.scalars().all()

    async def update(self, song: Song) -> Song:
        await self.session.commit()
        await self.session.refresh(song)
        return song

    async def delete(self, song: Song) -> None:
        await self.session.delete(song)
        await self.session.commit()

    async def get_artist_id_by_song(self, song_id: int) -> int | None:
        stmt = (
            select(Album.artist_id)
            .select_from(Song)
            .join(Album, Album.id == Song.album_id)
            .where(Song.id == song_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
