# song_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from database.models import Song, Album, Artist, User

class SongRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_title_ilike(self, query: str, limit: int, offset: int):
        stmt = (
            select(Song)
            .options(
                selectinload(Song.album).selectinload(Album.artist).selectinload(Artist.user),
                selectinload(Song.artists).selectinload(Artist.user)
            )
            .where(Song.title.ilike(f"%{query}%"))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()