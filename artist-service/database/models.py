from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
    JSON,
    text,
)
from sqlalchemy.orm import relationship
from database.connection import Base


class User(Base):
    __tablename__ = "users"
    # Añadimos el argumento de tabla para especificar el esquema
    __table_args__ = {"schema": "music_streaming"}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")
    birthdate = Column(Date, nullable=True)

    # 🔧 Corrección: mejor usar CURRENT_TIMESTAMP para Postgres
    registerdate = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    last_username_change = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    last_email_change = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    last_password_change = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # relación con Artist
    artist_profile = relationship("Artist", back_populates="user", uselist=False)


class Artist(Base):
    __tablename__ = "artists"
    __table_args__ = {"schema": "music_streaming"}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("music_streaming.users.id"), unique=True, nullable=False
    )
    artist_name = Column(Text, unique=True, nullable=False)
    bio = Column(Text, nullable=True)
    profile_pic = Column(String, nullable=True)
    social_links = Column(JSON, nullable=True)

    created_at = Column(Date, server_default=text("CURRENT_DATE"), nullable=False)
    updated_at = Column(
        Date,
        server_default=text("CURRENT_DATE"),
        onupdate=text("CURRENT_DATE"),
        nullable=False,
    )

    # relaciones
    user = relationship("User", back_populates="artist_profile")
    albums = relationship(
        "Album", back_populates="artist", cascade="all, delete-orphan"
    )
    songs = relationship(
        "Song",
        secondary="music_streaming.song_artists",
        back_populates="artists",
    )


class Album(Base):
    __tablename__ = "albums"
    __table_args__ = {"schema": "music_streaming"}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    artist_id = Column(
        Integer, ForeignKey("music_streaming.artists.id"), nullable=False
    )
    title = Column(String, nullable=False)
    release_date = Column(Date, nullable=True)
    cover_url = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # relaciones
    artist = relationship("Artist", back_populates="albums")
    songs = relationship("Song", back_populates="album", cascade="all, delete-orphan")


class Song(Base):
    __tablename__ = "songs"
    __table_args__ = {"schema": "music_streaming"}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    album_id = Column(Integer, ForeignKey("music_streaming.albums.id"), nullable=False)
    genre_id = Column(Integer, ForeignKey("music_streaming.genres.id"), nullable=False)
    title = Column(String, nullable=False)
    duration = Column(Integer, nullable=True)
    audio_url = Column(Text, nullable=False)
    track_number = Column(Integer, nullable=True)

    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # relaciones
    album = relationship("Album", back_populates="songs")
    artists = relationship(
        "Artist",
        secondary="music_streaming.song_artists",
        back_populates="songs",
    )


class SongArtist(Base):
    __tablename__ = "song_artists"
    __table_args__ = {"schema": "music_streaming"}

    song_id = Column(Integer, ForeignKey("music_streaming.songs.id"), primary_key=True)
    artist_id = Column(
        Integer, ForeignKey("music_streaming.artists.id"), primary_key=True
    )
