from datetime import date
from infrastructure.db.models import Album, Song
from core.repositories.album_repository import AlbumRepository
from events.producer import publish_album_created_event, publish_album_updated_event
from core.services.artist_lookup import ArtistLookupService
import os
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from infrastructure.storage.s3_client import (
    upload_bytes_to_s3,
    build_s3_public_url,
    delete_from_s3,
    extract_s3_key_from_url,
)


class AlbumService:
    def __init__(self, repo: AlbumRepository):
        self.repo = repo

    def _save_cover_image(
        self,
        artist_id: int,
        album_id: int,
        image_data: bytes,
        filename: str | None = None,
    ) -> str:
        """Sube una imagen de portada a S3"""
        ext = ".png"
        if filename:
            _, ext_candidate = os.path.splitext(filename)
            if ext_candidate.lower() in [".png", ".jpg", ".jpeg"]:
                ext = ext_candidate.lower()

        filename = f"cover{ext}"
        key = f"{artist_id}/{album_id}/{filename}"
        content_type = "image/png" if ext == ".png" else "image/jpeg"

        upload_bytes_to_s3(settings.aws_s3_bucket, key, image_data, content_type)

        cover_url = build_s3_public_url(
            settings.aws_s3_bucket, settings.aws_region, key
        )
        print(f"[✓] Imagen subida a S3: {cover_url}")
        return cover_url

    def _delete_cover_image(self, cover_url: str) -> bool:
        """Elimina la imagen de portada de S3"""
        key = extract_s3_key_from_url(
            cover_url, settings.aws_s3_bucket, settings.aws_region
        )
        if key:
            return delete_from_s3(settings.aws_s3_bucket, key)
        return False

    async def create_album(
        self,
        title: str,
        user_id: int,
        db: AsyncSession,
        release_date: date | None = None,
        cover_image: bytes | None = None,
        cover_filename: str | None = None,
    ) -> Album:
        """Crea un nuevo álbum"""
        artist_id = await ArtistLookupService.get_artist_id_by_user(user_id, db=db)
        if not artist_id:
            raise ValueError(f"No existe artista para el user_id {user_id}")

        release_date = release_date or date.today()

        # 1. Crear el álbum sin portada
        album = Album(
            title=title,
            artist_id=artist_id,
            release_date=release_date,
        )
        album = await self.repo.create(album)

        # 2. Guardar la portada en S3 si se envía
        if cover_image:
            cover_url = self._save_cover_image(
                artist_id, album.id, cover_image, cover_filename
            )
            album.cover_url = cover_url
            album = await self.repo.update(album)

        # 3. Publicar evento
        await publish_album_created_event(
            {
                "id": album.id,
                "title": album.title,
                "artist_id": album.artist_id,
                "release_date": album.release_date.isoformat()
                if album.release_date
                else None,
                "cover_url": album.cover_url,
            }
        )

        return album

    async def get_album(self, album_id: int) -> Album | None:
        """Obtiene un álbum por ID"""
        return await self.repo.get_by_id(album_id)

    async def list_albums_by_user(self, user_id: int, db: AsyncSession) -> list[Album]:
        """Lista todos los álbumes de un usuario"""
        artist_id = await ArtistLookupService.get_artist_id_by_user(user_id, db=db)
        if not artist_id:
            return []
        return list(await self.repo.list_by_artist(artist_id))

    async def update_album(
        self,
        album: Album,
        title: str | None = None,
        release_date: date | None = None,
        cover_image: bytes | None = None,
        cover_filename: str | None = None,
    ) -> Album:
        """Actualiza un álbum existente"""
        if title:
            album.title = title
        if release_date:
            album.release_date = release_date

        # Si se envía nueva imagen, eliminar la anterior de S3 y subir la nueva
        if cover_image:
            # Eliminar imagen anterior si existe
            if album.cover_url:
                self._delete_cover_image(album.cover_url)

            # Subir nueva imagen a S3
            cover_url = self._save_cover_image(
                album.artist_id, album.id, cover_image, cover_filename
            )
            album.cover_url = cover_url

        album = await self.repo.update(album)

        await publish_album_updated_event(
            {
                "id": album.id,
                "title": album.title,
                "artist_id": album.artist_id,
                "release_date": album.release_date.isoformat()
                if album.release_date
                else None,
                "cover_url": album.cover_url,
            }
        )

        return album

    async def delete_album(self, album: Album) -> None:
        """Elimina un álbum y todos sus archivos de S3"""
        # Eliminar imagen de portada de S3 si existe
        if album.cover_url:
            self._delete_cover_image(album.cover_url)

        # Eliminar archivos de audio de todas las canciones del álbum
        songs = await self.repo.list_songs_by_album(album.id)
        for song in songs:
            if song.audio_url:
                key = extract_s3_key_from_url(
                    song.audio_url, settings.aws_s3_bucket, settings.aws_region
                )
                if key:
                    delete_from_s3(settings.aws_s3_bucket, key)

        # Eliminar álbum de la base de datos
        await self.repo.delete(album)

    async def list_songs_by_album(self, album_id: int) -> list[Song]:
        """Lista todas las canciones de un álbum"""
        return list(await self.repo.list_songs_by_album(album_id))

    async def get_artist_albums_with_info(self, artist_id: int) -> list[dict]:
        """Obtiene todos los álbumes de un artista con información completa"""
        albums = await self.repo.get_albums_with_artist_info(artist_id)

        for album in albums:
            songs = await self.repo.list_songs_by_album(album["id"])
            album["total_songs"] = len(songs)

            if album["release_date"]:
                album["release_date"] = album["release_date"].isoformat()
            if album["created_at"]:
                album["created_at"] = album["created_at"].isoformat()
            if album["updated_at"]:
                album["updated_at"] = album["updated_at"].isoformat()

        return albums
