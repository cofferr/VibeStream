# album_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from database.models import Album, Artist, User

class AlbumRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_title_ilike(self, query: str, limit: int, offset: int):
        stmt = (
            select(Album)
            .options(
                selectinload(Album.artist).selectinload(Artist.user)
            )
            .where(Album.title.ilike(f"%{query}%"))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()