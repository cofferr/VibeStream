# core/repositories/playlist_repository.py
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy import func as sql_func
from database.models import Playlist, PlaylistSong
from typing import Optional, Dict, Any, List
from datetime import date
from config import settings


class PlaylistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_playlist(self, playlist: Playlist) -> Playlist:
        """Crear una playlist - los timestamps se manejan automáticamente"""
        self.session.add(playlist)
        await self.session.commit()
        await self.session.refresh(playlist)
        return playlist

    async def update_playlist(
        self,
        playlist_id: int,
        user_id: int,  # Añadido para verificar permisos
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Playlist]:
        """Editar una playlist - updated_at se actualiza automáticamente"""
        # Buscar la playlist verificando que pertenezca al usuario
        stmt = select(Playlist).where(
            Playlist.id == playlist_id, Playlist.user_id == user_id
        )
        result = await self.session.execute(stmt)
        playlist = result.scalar_one_or_none()

        if not playlist:
            return None

        # Actualizar solo los campos proporcionados
        if name is not None:
            playlist.name = name
        if description is not None:
            playlist.description = description

        # El updated_at se actualiza automáticamente por la configuración onupdate
        await self.session.commit()
        await self.session.refresh(playlist)
        return playlist

    async def delete_playlist(self, playlist_id: int, user_id: int) -> bool:
        """Eliminar una playlist verificando que pertenezca al usuario"""
        # Primero verificar que la playlist existe y pertenece al usuario
        stmt = select(Playlist).where(
            Playlist.id == playlist_id, Playlist.user_id == user_id
        )
        result = await self.session.execute(stmt)
        playlist = result.scalar_one_or_none()

        if not playlist:
            return False

        # Eliminar las relaciones con canciones (cascade debería manejar esto automáticamente)
        await self.session.execute(
            delete(PlaylistSong).where(PlaylistSong.playlist_id == playlist_id)
        )

        # Eliminar la playlist
        await self.session.delete(playlist)
        await self.session.commit()
        return True

    async def get_playlist_by_id(
        self, playlist_id: int, user_id: int
    ) -> Optional[Playlist]:
        """Obtener una playlist por ID verificando permisos"""
        stmt = select(Playlist).where(
            Playlist.id == playlist_id, Playlist.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_playlist_songs(self, playlist_id: int, user_id: int) -> List[Dict[str, Any]]:
        """
        Obtener todas las canciones de una playlist con formato específico:
        Incluye URLs completas para cover y audio
        """
        from database.models import Song, Album, Artist

        # Primero verificar que la playlist pertenece al usuario
        playlist = await self.get_playlist_by_id(playlist_id, user_id)
        if not playlist:
            return []

        # Base URL para los archivos (configurable vía FILES_BASE_URL)
        BASE_URL = getattr(settings, "files_base_url", "http://localhost:8002/files")

        # Consulta optimizada para obtener toda la información necesaria
        stmt = (
            select(
                Song.id.label("song_id"),
                Song.title.label("song_title"),
                Song.audio_url,
                Song.duration,
                Album.cover_url,
                Album.title.label("album_title"),
                Artist.artist_name,
                Artist.id.label("artist_id"),
                PlaylistSong.added_at,
            )
            .select_from(PlaylistSong)
            .join(Song, PlaylistSong.song_id == Song.id)
            .join(Album, Song.album_id == Album.id)
            .join(Artist, Album.artist_id == Artist.id)
            .where(PlaylistSong.playlist_id == playlist_id)
            .order_by(PlaylistSong.added_at.asc())
        )

        result = await self.session.execute(stmt)
        songs_data = result.fetchall()

        # Formatear la respuesta con URLs completas
        formatted_songs = []
        for song_data in songs_data:
            # Construir URLs completas
            cover_url = f"{BASE_URL}{song_data.cover_url}" if song_data.cover_url else None
            audio_url = f"{BASE_URL}{song_data.audio_url}" if song_data.audio_url else None

            formatted_songs.append(
                {
                    "id": song_data.song_id,
                    "title": song_data.song_title,
                    "artist_name": song_data.artist_name,
                    "duration": song_data.duration,
                    "album_title": song_data.album_title,
                    "album_cover": cover_url,
                    "audio_url": audio_url,
                    "artist_id": song_data.artist_id,
                    "added_at": song_data.added_at.isoformat() if song_data.added_at else None,
                }
            )

        return formatted_songs

    async def add_song_to_playlist(
        self, playlist_id: int, song_id: int, user_id: int
    ) -> bool:
        """Añadir una canción a la playlist verificando permisos"""
        try:
            # Verificar que la playlist pertenece al usuario
            playlist = await self.get_playlist_by_id(playlist_id, user_id)
            if not playlist:
                return False

            # Verificar que la canción existe
            from database.models import Song

            stmt = select(Song).where(Song.id == song_id)
            result = await self.session.execute(stmt)
            song = result.scalar_one_or_none()
            if not song:
                return False

            # Verificar si la canción ya está en la playlist
            stmt = select(PlaylistSong).where(
                PlaylistSong.playlist_id == playlist_id, PlaylistSong.song_id == song_id
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                return True  # Ya existe, no es error

            # Añadir la canción a la playlist
            playlist_song = PlaylistSong(
                playlist_id=playlist_id, song_id=song_id, added_at=date.today()
            )

            self.session.add(playlist_song)
            await self.session.commit()
            return True

        except Exception:
            await self.session.rollback()
            return False

    async def remove_song_from_playlist(
        self, playlist_id: int, song_id: int, user_id: int
    ) -> bool:
        """Eliminar una canción de la playlist verificando permisos"""
        try:
            # Verificar que la playlist pertenece al usuario
            playlist = await self.get_playlist_by_id(playlist_id, user_id)
            if not playlist:
                return False

            # Buscar y eliminar la relación
            stmt = select(PlaylistSong).where(
                PlaylistSong.playlist_id == playlist_id, PlaylistSong.song_id == song_id
            )
            result = await self.session.execute(stmt)
            playlist_song = result.scalar_one_or_none()

            if not playlist_song:
                return False

            await self.session.delete(playlist_song)
            await self.session.commit()
            return True

        except Exception:
            await self.session.rollback()
            return False

    async def get_user_playlists(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> List[Playlist]:
        """
        Obtener todas las playlists de un usuario con paginación

        Args:
            user_id: ID del usuario
            limit: Número máximo de playlists a retornar (default: 50)
            offset: Número de playlists a saltar para paginación (default: 0)

        Returns:
            Lista de playlists del usuario
        """
        try:
            stmt = (
                select(Playlist)
                .where(Playlist.user_id == user_id)
                .order_by(Playlist.created_at.desc())  # Las más recientes primero
                .offset(offset)
                .limit(limit)
            )

            result = await self.session.execute(stmt)
            playlists = result.scalars().all()
            return list(playlists)

        except Exception:
            return []

    async def count_user_playlists(self, user_id: int) -> int:
        """Contar el total de playlists de un usuario"""
        try:
            from sqlalchemy import func as sql_func

            stmt = select(sql_func.count(Playlist.id)).where(
                Playlist.user_id == user_id
            )
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception:
            return 0
