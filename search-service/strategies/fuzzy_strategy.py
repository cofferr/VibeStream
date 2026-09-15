# strategies/fuzzy_strategy.py
from rapidfuzz import fuzz
from typing import List, Tuple
from strategies.base_strategy import SearchStrategy
from repositories.song_repository import SongRepository
from repositories.album_repository import AlbumRepository
from repositories.artist_repository import ArtistRepository
from sqlalchemy.ext.asyncio import AsyncSession

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
            except Exception as e:
                print(f"Error filtrando objeto: {e}")
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

        try:
            print(f"🎵 Buscando canciones con: '{query}'")
            songs = await song_repo.get_by_title_ilike(query, limit * 3, offset_songs)
            print(f"🎵 Canciones encontradas: {len(songs)}")

            print(f"📀 Buscando álbumes con: '{query}'")
            albums = await album_repo.get_by_title_ilike(query, limit * 3, offset_albums)
            print(f"📀 Álbumes encontrados: {len(albums)}")

            print(f"👤 Buscando artistas con: '{query}'")
            artists = await artist_repo.search_by_name(query, limit * 3, offset_artists)
            print(f"👤 Artistas encontrados: {len(artists)}")

            # Filtrar usando fuzzy matching sobre los objetos
            filtered_songs = await self._filter_objects(songs, query, "title")
            filtered_albums = await self._filter_objects(albums, query, "title")
            filtered_artists = await self._filter_objects(artists, query, "artist_name")

            print(f"🎯 Resultados después de filtro fuzzy: {len(filtered_songs)} canciones, {len(filtered_albums)} álbumes, {len(filtered_artists)} artistas")

            return (
                filtered_songs[:limit],
                filtered_albums[:limit],
                filtered_artists[:limit],
            )

        except Exception as e:
            print(f"❌ Error en búsqueda fuzzy: {e}")
            import traceback
            traceback.print_exc()
            return [], [], []