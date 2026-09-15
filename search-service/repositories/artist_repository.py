# artist_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from database.models import Artist, User

class ArtistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_by_name(self, query: str, limit: int, offset: int):
        stmt = (
            select(Artist)
            .options(selectinload(Artist.user))
            .where(Artist.artist_name.ilike(f"%{query}%"))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()