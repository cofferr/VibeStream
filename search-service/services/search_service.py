# services/search_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from strategies.base_strategy import SearchStrategy
from services.serializers import serialize_song, serialize_album, serialize_artist

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
        try:
            songs, albums, artists = await self.strategy.search(
                session, query, limit, offset_songs, offset_albums, offset_artists
            )

            # Serializar resultados de forma segura
            serialized_songs = []
            for song in songs:
                try:
                    serialized = serialize_song(song)
                    if serialized:
                        serialized_songs.append(serialized)
                except Exception as e:
                    print(f"❌ Error serializando canción {getattr(song, 'id', 'unknown')}: {e}")
                    continue

            serialized_albums = []
            for album in albums:
                try:
                    serialized = serialize_album(album)
                    if serialized:
                        serialized_albums.append(serialized)
                except Exception as e:
                    print(f"❌ Error serializando álbum {getattr(album, 'id', 'unknown')}: {e}")
                    continue

            serialized_artists = []
            for artist in artists:
                try:
                    serialized = serialize_artist(artist)
                    if serialized:
                        serialized_artists.append(serialized)
                except Exception as e:
                    print(f"❌ Error serializando artista {getattr(artist, 'id', 'unknown')}: {e}")
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

        except Exception as e:
            print(f"❌ Error en SearchService: {e}")
            import traceback
            traceback.print_exc()
            return {
                "songs": {"page": 1, "results": [], "total": 0},
                "albums": {"page": 1, "results": [], "total": 0},
                "artists": {"page": 1, "results": [], "total": 0},
            }