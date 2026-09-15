from sqlalchemy.ext.asyncio import AsyncSession
from services.repositories.artist_repository import ArtistRepository
from events.events import (
    publish_artist_created_event,
    publish_artist_updated_event,
    publish_artist_deleted_event,
)
from models.artist import (
    ArtistCreateSchema,
    ArtistUpdateSchema,
    ArtistResponseSchema,
)
import asyncio
import logging
from fastapi import UploadFile
from typing import Optional
from utils.file_uploader import FileUploader
from vibestream_common.http_client import InternalHTTPClient, InternalServiceError
from config import settings

logger = logging.getLogger(__name__)

content_client = InternalHTTPClient(settings.content_service_url)


class ArtistService:
    @staticmethod
    async def register_artist(
        db: AsyncSession,
        user_id: int,
        data: ArtistCreateSchema,
        profile_pic_file: Optional[UploadFile] = None,
    ) -> ArtistResponseSchema:
        # Evitamos crear si ya existe un artista para este user_id
        existing_artist = await ArtistRepository.get_by_user_id(db, user_id)
        if existing_artist:
            return ArtistResponseSchema.model_validate(
                existing_artist, from_attributes=True
            )

        # Creamos el artista primero para obtener el artist_id
        artist = await ArtistRepository.create(db, data, user_id)

        # 🔹 AHORA que tenemos el artist_id, subimos la foto a su carpeta utils
        if profile_pic_file:
            uploaded_url = await FileUploader.upload_profile_picture(
                profile_pic_file,
                artist.id,  # 🔹 NO convertir - usar directamente
            )
            # 🔹 Crear un ArtistUpdateSchema para la actualización
            update_data = ArtistUpdateSchema(profile_pic=uploaded_url)
            artist = await ArtistRepository.update(db, artist, update_data)

        artist_schema = ArtistResponseSchema.model_validate(
            artist, from_attributes=True
        )

        # 🚀 Publicamos el evento de artista creado
        asyncio.create_task(publish_artist_created_event(artist_schema.model_dump()))

        return artist_schema

    @staticmethod
    async def get_artist_by_user(
        db: AsyncSession, user_id: int
    ) -> ArtistResponseSchema | None:
        artist = await ArtistRepository.get_by_user_id(db, user_id)
        return (
            ArtistResponseSchema.model_validate(artist, from_attributes=True)
            if artist
            else None
        )

    @staticmethod
    async def get_artist_by_id(
        db: AsyncSession, artist_id: int
    ) -> ArtistResponseSchema | None:
        """Lectura pública por id, consumida por content-service,
        search-service y subscription-service (Fase 3: propiedad de datos
        por servicio)."""
        artist = await ArtistRepository.get_by_id(db, artist_id)
        return (
            ArtistResponseSchema.model_validate(artist, from_attributes=True)
            if artist
            else None
        )

    @staticmethod
    async def update_artist_by_user(
        db: AsyncSession,
        user_id: int,
        data: ArtistUpdateSchema,
        profile_pic_file: Optional[UploadFile] = None,
    ) -> ArtistResponseSchema | None:
        artist = await ArtistRepository.get_by_user_id(db, user_id)
        if not artist:
            return None

        # 🔹 Si viene archivo, lo subimos a la carpeta utils del artista
        if profile_pic_file:
            uploaded_url = await FileUploader.upload_profile_picture(
                profile_pic_file,
                artist.id,  # 🔹 NO convertir - usar directamente
            )
            data.profile_pic = uploaded_url

        updated = await ArtistRepository.update(db, artist, data)
        artist_schema = ArtistResponseSchema.model_validate(
            updated, from_attributes=True
        )

        asyncio.create_task(publish_artist_updated_event(artist_schema.model_dump()))

        return artist_schema

    @staticmethod
    async def delete_artist_by_user(db: AsyncSession, user_id: int) -> bool:
        artist = await ArtistRepository.get_by_user_id(db, user_id)
        if not artist:
            return False

        # Los álbumes/canciones del artista ya no son tablas de este
        # servicio (Fase 3): se borran en content-service antes de borrar
        # el artista local, para no dejar huérfanos.
        try:
            await content_client.delete(f"/albums/artist/{artist.id}")
        except InternalServiceError:
            logger.exception(
                "No se pudo eliminar el contenido del artista %s en content-service",
                artist.id,
            )
            raise

        artist_id = artist.id
        await ArtistRepository.delete(db, artist)

        # captura artist_id antes del delete: tras el commit el objeto
        # queda expirado y acceder a artist.id dispararía un refresh
        # contra una fila que ya no existe
        asyncio.create_task(publish_artist_deleted_event(artist_id))

        return True
