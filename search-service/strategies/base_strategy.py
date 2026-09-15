from abc import ABC, abstractmethod
from typing import Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Song, Album, Artist


class SearchStrategy(ABC):
    @abstractmethod
    async def search(
        self,
        session: AsyncSession,
        query: str,
        limit: int,
        offset_songs: int,
        offset_albums: int,
        offset_artists: int,
    ) -> Tuple[List[Song], List[Album], List[Artist]]: ...
