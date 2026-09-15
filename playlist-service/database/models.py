# database/models.py - VERSIÓN MÍNIMA QUE FUNCIONA
from sqlalchemy import Integer, String, Text, Date, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import date

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String)
    username: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String)
    password: Mapped[Optional[str]] = mapped_column(String)
    role: Mapped[Optional[str]] = mapped_column(String)
    birthdate: Mapped[Optional[date]] = mapped_column(Date)
    registerdate: Mapped[Optional[date]] = mapped_column(Date)


class Playlist(Base):
    __tablename__ = "playlists"
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("music_streaming.users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    updated_at: Mapped[date] = mapped_column(
        Date, server_default=func.current_date(), onupdate=func.current_date()
    )


class PlaylistSong(Base):
    __tablename__ = "playlist_songs"
    __table_args__ = {"schema": "music_streaming"}

    playlist_id: Mapped[int] = mapped_column(
        ForeignKey("music_streaming.playlists.id"), primary_key=True
    )
    song_id: Mapped[int] = mapped_column(
        ForeignKey("music_streaming.songs.id"), primary_key=True
    )
    added_at: Mapped[date] = mapped_column(Date, server_default=func.current_date())


class Artist(Base):
    __tablename__ = "artists"
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("music_streaming.users.id"), nullable=False, unique=True
    )
    bio: Mapped[Optional[str]] = mapped_column(Text)
    profile_pic: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    updated_at: Mapped[date] = mapped_column(
        Date, server_default=func.current_date(), onupdate=func.current_date()
    )
    artist_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class Album(Base):
    __tablename__ = "albums"
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artist_id: Mapped[int] = mapped_column(
        ForeignKey("music_streaming.artists.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    release_date: Mapped[Optional[date]] = mapped_column(Date)
    cover_url: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    updated_at: Mapped[date] = mapped_column(
        Date, server_default=func.current_date(), onupdate=func.current_date()
    )


class Song(Base):
    __tablename__ = "songs"
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    album_id: Mapped[int] = mapped_column(
        ForeignKey("music_streaming.albums.id"), nullable=False
    )
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("music_streaming.genres.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    duration: Mapped[Optional[int]] = mapped_column(Integer)
    audio_url: Mapped[str] = mapped_column(Text, nullable=False)
    track_number: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    updated_at: Mapped[date] = mapped_column(
        Date, server_default=func.current_date(), onupdate=func.current_date()
    )
