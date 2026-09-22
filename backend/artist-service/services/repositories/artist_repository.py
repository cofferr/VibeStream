from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.models import Artist
from models.artist import ArtistCreateSchema, ArtistUpdateSchema


class ArtistRepository:
    @staticmethod
    async def create(
        db: AsyncSession, data: ArtistCreateSchema, user_id: int
    ) -> Artist:
        new_artist = Artist(
            user_id=user_id,
            artist_name=data.artist_name,  # ✅ nuevo campo obligatorio
            bio=data.bio,
            profile_pic=str(data.profile_pic) if data.profile_pic else None,
            social_links=data.social_links if data.social_links else {},
        )
        db.add(new_artist)
        await db.commit()
        await db.refresh(new_artist)
        return new_artist

    @staticmethod
    async def get_by_id(db: AsyncSession, artist_id: int) -> Artist | None:
        result = await db.execute(select(Artist).where(Artist.id == artist_id))
        return result.scalars().first()

    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id: int) -> Artist | None:
        result = await db.execute(select(Artist).where(Artist.user_id == user_id))
        return result.scalars().first()

    @staticmethod
    async def update(
        db: AsyncSession, artist: Artist, data: ArtistUpdateSchema
    ) -> Artist:
        _artist = cast(Any, artist)

        if data.artist_name is not None:
            _artist.artist_name = data.artist_name  # ✅ ahora se puede actualizar
        if data.bio is not None:
            _artist.bio = data.bio
        if data.profile_pic is not None:
            _artist.profile_pic = str(data.profile_pic)
        if data.social_links is not None:
            _artist.social_links = data.social_links

        await db.commit()
        await db.refresh(artist)
        return artist

    @staticmethod
    async def delete(db: AsyncSession, artist: Artist) -> None:
        """Elimina el artista de este servicio. Sus álbumes/canciones ya no
        son tablas locales (Fase 3): el cascade en content-service lo hace
        ArtistService.delete_artist_by_user antes de llamar aquí."""
        await db.delete(artist)
        await db.commit()
