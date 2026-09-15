from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from infrastructure.db.models import Album, Artist, Song
from collections.abc import Sequence
from typing import Dict, Any, List


class AlbumRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, album: Album) -> Album:
        self.session.add(album)
        await self.session.commit()
        await self.session.refresh(album)
        return album

    async def get_by_id(self, album_id: int) -> Album | None:
        stmt = (
            select(Album).where(Album.id == album_id).execution_options(prepared=False)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_artist(self, artist_id: int) -> Sequence[Album]:
        stmt = (
            select(Album)
            .where(Album.artist_id == artist_id)
            .execution_options(prepared=False)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, album: Album) -> Album:
        await self.session.commit()
        await self.session.refresh(album)
        return album

    async def delete(self, album: Album) -> None:
        # 🔹 Borrar todas las canciones del álbum antes
        await self.session.execute(delete(Song).where(Song.album_id == album.id))

        # 🔹 Ahora sí borrar el álbum
        await self.session.delete(album)

        await self.session.commit()

    async def get_artist_id_by_album(self, album_id: int) -> int | None:
        stmt = select(Album.artist_id).where(Album.id == album_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_songs_by_album(self, album_id: int) -> Sequence[Song]:
        stmt = select(Song).where(Song.album_id == album_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_albums_with_artist_info(self, artist_id: int) -> list[dict]:
        """Obtiene todos los álbumes de un artista con información completa"""
        stmt = (
            select(
                Album.id,
                Album.title,
                Album.release_date,
                Album.cover_url,
                Album.created_at,
                Album.updated_at,
                Artist.artist_name,
                Artist.id.label("artist_id"),
            )
            .join(Artist, Album.artist_id == Artist.id)
            .where(Album.artist_id == artist_id)
            .order_by(Album.release_date.desc().nulls_last(), Album.created_at.desc())
            .execution_options(prepared=False)
        )

        result = await self.session.execute(stmt)

        # Convertir los resultados a lista de diccionarios
        albums = []
        for row in result:
            albums.append(
                {
                    "id": row.id,
                    "title": row.title,
                    "release_date": row.release_date,
                    "cover_url": row.cover_url,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                    "artist_id": row.artist_id,
                    "artist_name": row.artist_name,
                }
            )

        return albums
