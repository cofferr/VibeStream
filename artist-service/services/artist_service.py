from sqlalchemy.ext.asyncio import AsyncSession
from services.repositories.artist_repository import ArtistRepository
from events.events import publish_artist_created_event
from models.artist import (
    ArtistCreateSchema,
    ArtistUpdateSchema,
    ArtistResponseSchema,
)
import asyncio
from fastapi import UploadFile
from typing import Optional
from utils.file_uploader import FileUploader


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
        return ArtistResponseSchema.model_validate(updated, from_attributes=True)

    @staticmethod
    async def delete_artist_by_user(db: AsyncSession, user_id: int) -> bool:
        artist = await ArtistRepository.get_by_user_id(db, user_id)
        if not artist:
            return False
        await ArtistRepository.delete(db, artist)
        return True
