# strategies/fuzzy_strategy.py
import logging
from typing import List, Tuple

from rapidfuzz import fuzz
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.album_repository import AlbumRepository
from repositories.artist_repository import ArtistRepository
from repositories.song_repository import SongRepository
from strategies.base_strategy import SearchStrategy

logger = logging.getLogger(__name__)


class FuzzySearchStrategy(SearchStrategy):
    def __init__(self, threshold: int = 70):
        self.threshold = threshold

    async def _filter_objects(self, objects, query: str, field_name: str) -> List:
        """
        Filtra una lista de OBJETOS usando fuzzy matching sobre un campo específico.
        """
        filtered = []
        for obj in objects:
            try:
                # Obtener el valor del campo usando getattr
                field_value = getattr(obj, field_name, None)
                if field_value:
                    similarity = fuzz.partial_ratio(
                        query.lower(), str(field_value).lower()
                    )
                    if similarity >= self.threshold:
                        filtered.append((obj, similarity))
            except Exception:
                logger.exception(
                    "Error filtrando objeto %s por campo %r",
                    getattr(obj, "id", "unknown"),
                    field_name,
                )
                continue

        # Ordenar por similitud (mayor a menor) y retornar solo los objetos
        filtered.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in filtered]

    async def search(
        self,
        session: AsyncSession,
        query: str,
        limit: int,
        offset_songs: int,
        offset_albums: int,
        offset_artists: int,
    ) -> Tuple[List, List, List]:
        song_repo = SongRepository(session)
        album_repo = AlbumRepository(session)
        artist_repo = ArtistRepository(session)

        songs = await song_repo.get_by_title_ilike(query, limit * 3, offset_songs)
        albums = await album_repo.get_by_title_ilike(query, limit * 3, offset_albums)
        artists = await artist_repo.search_by_name(query, limit * 3, offset_artists)

        # Filtrar usando fuzzy matching sobre los objetos (los 3 tipos de
        # entidad del índice usan "title" como campo de nombre principal)
        filtered_songs = await self._filter_objects(songs, query, "title")
        filtered_albums = await self._filter_objects(albums, query, "title")
        filtered_artists = await self._filter_objects(artists, query, "title")

        return (
            filtered_songs[:limit],
            filtered_albums[:limit],
            filtered_artists[:limit],
        )