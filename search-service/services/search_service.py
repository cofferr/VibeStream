# services/search_service.py
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from strategies.base_strategy import SearchStrategy
from services.serializers import serialize_song, serialize_album, serialize_artist

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, strategy: SearchStrategy):
        self.strategy = strategy

    async def search(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 5,
        offset_songs: int = 0,
        offset_albums: int = 0,
        offset_artists: int = 0,
    ) -> dict:
        # Un fallo real de búsqueda (BD, estrategia) se propaga al handler,
        # que responde 500 saneado — no debe simularse como "sin resultados".
        songs, albums, artists = await self.strategy.search(
            session, query, limit, offset_songs, offset_albums, offset_artists
        )

        # Serializar resultados de forma segura: un objeto individual
        # corrupto no debe tumbar toda la búsqueda, solo se omite y se loguea.
        serialized_songs = []
        for song in songs:
            try:
                serialized = serialize_song(song)
                if serialized:
                    serialized_songs.append(serialized)
            except Exception:
                logger.exception(
                    "Error serializando canción %s", getattr(song, "id", "unknown")
                )
                continue

        serialized_albums = []
        for album in albums:
            try:
                serialized = serialize_album(album)
                if serialized:
                    serialized_albums.append(serialized)
            except Exception:
                logger.exception(
                    "Error serializando álbum %s", getattr(album, "id", "unknown")
                )
                continue

        serialized_artists = []
        for artist in artists:
            try:
                serialized = serialize_artist(artist)
                if serialized:
                    serialized_artists.append(serialized)
            except Exception:
                logger.exception(
                    "Error serializando artista %s", getattr(artist, "id", "unknown")
                )
                continue

        return {
            "songs": {
                "page": (offset_songs // limit) + 1 if limit > 0 else 1,
                "results": serialized_songs,
                "total": len(serialized_songs)
            },
            "albums": {
                "page": (offset_albums // limit) + 1 if limit > 0 else 1,
                "results": serialized_albums,
                "total": len(serialized_albums)
            },
            "artists": {
                "page": (offset_artists // limit) + 1 if limit > 0 else 1,
                "results": serialized_artists,
                "total": len(serialized_artists)
            },
        }