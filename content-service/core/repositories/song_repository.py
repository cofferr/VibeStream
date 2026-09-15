from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from infrastructure.db.models import Song, Album, Artist
from collections.abc import Sequence


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
