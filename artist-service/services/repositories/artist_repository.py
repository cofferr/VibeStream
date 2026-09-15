from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import Artist, Album, Song, SongArtist
from models.artist import ArtistCreateSchema, ArtistUpdateSchema
from typing import Any, cast
from sqlalchemy import delete


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
        """
        Elimina un artista junto con:
        - Sus álbumes
        - Canciones de esos álbumes
        - Relaciones song_artists de esas canciones
        - Relaciones song_artists del artista en canciones de otros álbumes
        """

        # 1) Obtener álbumes del artista
        albums_res = await db.execute(select(Album).where(Album.artist_id == artist.id))
        albums = albums_res.scalars().all()

        for album in albums:
            # 2) Obtener canciones del álbum
            songs_res = await db.execute(select(Song).where(Song.album_id == album.id))
            songs = songs_res.scalars().all()

            for song in songs:
                # 2a) Eliminar relaciones song_artists de la canción
                await db.execute(
                    delete(SongArtist).where(SongArtist.song_id == song.id)
                )

                # 2b) Eliminar la canción
                await db.delete(song)

            # 2c) Eliminar el álbum
            await db.delete(album)

        # 3) Eliminar relaciones song_artists del artista en colaboraciones
        await db.execute(delete(SongArtist).where(SongArtist.artist_id == artist.id))

        # 4) Eliminar el artista
        await db.delete(artist)

        # 5) Confirmar cambios
        await db.commit()
