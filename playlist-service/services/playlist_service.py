# core/services/playlist_service.py
import logging
from typing import Any, Dict, List, Optional

from vibestream_common.http_client import InternalHTTPClient, InternalServiceError

from config import settings
from database.models import Playlist
from repositories.playlist_repository import PlaylistRepository

logger = logging.getLogger(__name__)


class PlaylistService:
    def __init__(self, repo: PlaylistRepository, user_id: int):
        self.repo = repo
        self.user_id = user_id
        self.content_client = InternalHTTPClient(settings.content_service_url)

    async def create_playlist(
        self, name: str, description: Optional[str] = None
    ) -> Playlist:
        """Crear una nueva playlist"""
        # Validación básica
        if not name or not name.strip():
            raise ValueError("El nombre de la playlist es requerido")

        # Crear el objeto playlist sin timestamps (se manejan automáticamente)
        playlist = Playlist(
            user_id=self.user_id,
            name=name.strip(),
            description=description.strip() if description else None,
        )

        return await self.repo.create_playlist(playlist)

    async def update_playlist(
        self,
        playlist_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Playlist]:
        """Actualizar una playlist existente"""
        # Validación básica
        if name is not None and not name.strip():
            raise ValueError("El nombre de la playlist no puede estar vacío")

        # Limpiar los datos si se proporcionan
        clean_name = name.strip() if name else None
        clean_description = description.strip() if description else None

        return await self.repo.update_playlist(
            playlist_id, self.user_id, clean_name, clean_description
        )

    async def delete_playlist(self, playlist_id: int) -> bool:
        """Eliminar una playlist"""
        return await self.repo.delete_playlist(playlist_id, self.user_id)

    async def get_playlist(self, playlist_id: int) -> Optional[Playlist]:
        """Obtener una playlist por ID"""
        return await self.repo.get_playlist_by_id(playlist_id, self.user_id)

    async def get_playlist_songs(self, playlist_id: int) -> List[Dict[str, Any]]:
        """
        Obtener todas las canciones de una playlist, enriquecidas con
        título/artista/portada vía el endpoint batch de content-service
        (playlist_songs solo guarda song_id; ya no hay join local a songs).

        Returns:
            Lista de canciones con formato: id, title, artist_name, duration, album_title, album_cover, audio_url, added_at
        """
        rows = await self.repo.get_playlist_song_rows(playlist_id, self.user_id)
        if not rows:
            return []

        added_at_by_song_id = {row.song_id: row.added_at for row in rows}
        song_ids = list(added_at_by_song_id.keys())

        try:
            response = await self.content_client.get(
                "/songs/batch", params={"ids": ",".join(str(i) for i in song_ids)}
            )
        except InternalServiceError:
            logger.exception(
                "No se pudo enriquecer playlist %s vía content-service", playlist_id
            )
            raise

        songs_by_id = {
            song["id"]: song
            for song in (response or {}).get("data", {}).get("songs", [])
        }

        formatted_songs = []
        for song_id, added_at in added_at_by_song_id.items():
            song = songs_by_id.get(song_id)
            if not song:
                # La canción fue borrada en content-service después de
                # añadirse a la playlist; se omite en vez de romper la vista.
                continue
            formatted_songs.append(
                {
                    "id": song["id"],
                    "title": song["title"],
                    "artist_name": song.get("artist_name"),
                    "artist_id": song.get("artist_id"),
                    "duration": song.get("duration"),
                    "album_title": song.get("album_title"),
                    "album_cover": song.get("album_cover_url"),
                    "audio_url": song.get("audio_url"),
                    "added_at": added_at.isoformat() if added_at else None,
                }
            )

        return formatted_songs

    async def add_song_to_playlist(
        self, playlist_id: int, song_id: int
    ) -> tuple[bool, str]:
        """
        Añadir una canción a la playlist. Valida contra content-service que
        la canción exista antes de guardar el song_id (ya no hay FK local).

        Returns:
            tuple[bool, str]: (success, message)
        """
        try:
            song = await self.content_client.get(f"/songs/{song_id}/enriched")
        except InternalServiceError:
            return False, "No se pudo validar la canción, intenta de nuevo."

        if not song:
            return False, "La canción no existe."

        success = await self.repo.add_song_to_playlist(
            playlist_id, song_id, self.user_id
        )

        if success:
            return True, "Canción añadida correctamente a la playlist"
        return (
            False,
            "No se pudo añadir la canción. Verifica que la playlist te pertenece.",
        )

    async def remove_song_from_playlist(
        self, playlist_id: int, song_id: int
    ) -> tuple[bool, str]:
        """
        Eliminar una canción de la playlist

        Returns:
            tuple[bool, str]: (success, message)
        """
        success = await self.repo.remove_song_from_playlist(
            playlist_id, song_id, self.user_id
        )

        if success:
            return True, "Canción eliminada correctamente de la playlist"
        return (
            False,
            "No se pudo eliminar la canción. Verifica que la playlist te pertenece y que la canción está en la playlist.",
        )

    async def get_user_playlists(self, page: int = 1, page_size: int = 20) -> dict:
        """
        Obtener todas las playlists del usuario con paginación

        Args:
            page: Número de página (default: 1)
            page_size: Tamaño de página (default: 20)

        Returns:
            Dict con playlists, información de paginación y metadatos
        """
        # Validar parámetros de paginación
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20

        offset = (page - 1) * page_size

        # Obtener playlists y total (RepositoryError se propaga al handler,
        # que responde 500 saneado en vez de simular un 200 con error)
        playlists = await self.repo.get_user_playlists(self.user_id, page_size, offset)
        total_playlists = await self.repo.count_user_playlists(self.user_id)

        # Calcular metadatos de paginación
        total_pages = (
            total_playlists + page_size - 1
        ) // page_size  # Redondeo hacia arriba
        has_next = page < total_pages
        has_previous = page > 1

        # Formatear playlists para la respuesta
        playlist_list = []
        for playlist in playlists:
            playlist_dict = {
                "id": playlist.id,
                "name": playlist.name,
                "description": playlist.description,
                "user_id": playlist.user_id,
                "created_at": playlist.created_at,
                "updated_at": playlist.updated_at,
            }
            playlist_list.append(playlist_dict)

        return {
            "playlists": playlist_list,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_items": total_playlists,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_previous": has_previous,
            },
            "summary": {
                "total_playlists": total_playlists,
                "showing": len(playlist_list),
            },
        }
