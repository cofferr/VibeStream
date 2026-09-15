from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, JSON, Table
from sqlalchemy.orm import relationship
from database.connection import Base

# Tabla intermedia para relación many-to-many
song_artists = Table(
    "song_artists",
    Base.metadata,
    Column(
        "song_id", Integer, ForeignKey("music_streaming.songs.id"), primary_key=True
    ),
    Column(
        "artist_id", Integer, ForeignKey("music_streaming.artists.id"), primary_key=True
    ),
    schema="music_streaming",
)


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "music_streaming"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    username = Column(String, unique=True, index=True)
    artist = relationship("Artist", back_populates="user", uselist=False)


class Artist(Base):
    __tablename__ = "artists"
    __table_args__ = {"schema": "music_streaming"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("music_streaming.users.id"), unique=True, nullable=False
    )
    artist_name = Column(String, nullable=False, unique=True)
    bio = Column(Text)
    profile_pic = Column(Text)
    social_links = Column(JSON)
    created_at = Column(Date)
    updated_at = Column(Date)

    albums = relationship("Album", back_populates="artist")
    user = relationship("User", back_populates="artist", uselist=False)
    songs = relationship("Song", secondary=song_artists, back_populates="artists")


class Album(Base):
    __tablename__ = "albums"
    __table_args__ = {"schema": "music_streaming"}

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(
        Integer, ForeignKey("music_streaming.artists.id"), nullable=False
    )
    title = Column(String, nullable=False)
    release_date = Column(Date)
    cover_url = Column(Text)
    created_at = Column(Date)
    updated_at = Column(Date)

    artist = relationship("Artist", back_populates="albums")
    songs = relationship("Song", back_populates="album")


class Song(Base):
    __tablename__ = "songs"
    __table_args__ = {"schema": "music_streaming"}

    id = Column(Integer, primary_key=True, index=True)
    album_id = Column(Integer, ForeignKey("music_streaming.albums.id"), nullable=False)
    genre_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    duration = Column(Integer)
    audio_url = Column(Text, nullable=False)
    track_number = Column(Integer)
    created_at = Column(Date)
    updated_at = Column(Date)

    album = relationship("Album", back_populates="songs")
    artists = relationship("Artist", secondary=song_artists, back_populates="songs")
