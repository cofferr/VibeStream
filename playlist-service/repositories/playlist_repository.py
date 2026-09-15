# core/repositories/playlist_repository.py
import logging
from datetime import date
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Playlist, PlaylistSong
from errors import RepositoryError

logger = logging.getLogger(__name__)


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

    async def get_playlist_song_rows(
        self, playlist_id: int, user_id: int
    ) -> List[PlaylistSong]:
        """Obtiene las filas playlist_songs (solo song_id + added_at) de una
        playlist propia. El enriquecimiento con título/artista/portada se
        hace en el service vía el endpoint batch de content-service, ya que
        songs ya no es una tabla de este servicio."""
        playlist = await self.get_playlist_by_id(playlist_id, user_id)
        if not playlist:
            return []

        stmt = (
            select(PlaylistSong)
            .where(PlaylistSong.playlist_id == playlist_id)
            .order_by(PlaylistSong.added_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_song_to_playlist(
        self, playlist_id: int, song_id: int, user_id: int
    ) -> bool:
        """Añadir una canción a la playlist verificando permisos. La
        existencia de la canción en content-service la valida el service
        antes de llamar aquí (ya no hay FK local a songs)."""
        try:
            # Verificar que la playlist pertenece al usuario
            playlist = await self.get_playlist_by_id(playlist_id, user_id)
            if not playlist:
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

        except Exception as e:
            await self.session.rollback()
            logger.exception(
                "Error de BD añadiendo canción %s a playlist %s", song_id, playlist_id
            )
            raise RepositoryError("No se pudo añadir la canción a la playlist") from e

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

        except Exception as e:
            await self.session.rollback()
            logger.exception(
                "Error de BD eliminando canción %s de playlist %s", song_id, playlist_id
            )
            raise RepositoryError("No se pudo eliminar la canción de la playlist") from e

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

        except Exception as e:
            logger.exception("Error de BD obteniendo playlists de usuario %s", user_id)
            raise RepositoryError("No se pudieron obtener las playlists") from e

    async def count_user_playlists(self, user_id: int) -> int:
        """Contar el total de playlists de un usuario"""
        try:
            from sqlalchemy import func as sql_func

            stmt = select(sql_func.count(Playlist.id)).where(
                Playlist.user_id == user_id
            )
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.exception("Error de BD contando playlists de usuario %s", user_id)
            raise RepositoryError("No se pudieron contar las playlists") from e
