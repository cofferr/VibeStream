# song_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import SearchIndexEntry


class SongRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_title_ilike(self, query: str, limit: int, offset: int):
        stmt = (
            select(SearchIndexEntry)
            .where(
                SearchIndexEntry.entity_type == "song",
                SearchIndexEntry.title.ilike(f"%{query}%"),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
