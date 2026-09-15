# artist_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import SearchIndexEntry


class ArtistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_by_name(self, query: str, limit: int, offset: int):
        stmt = (
            select(SearchIndexEntry)
            .where(
                SearchIndexEntry.entity_type == "artist",
                SearchIndexEntry.title.ilike(f"%{query}%"),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
