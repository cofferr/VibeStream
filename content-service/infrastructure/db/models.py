import datetime

from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


# Tabla de asociación many-to-many entre songs y artists
# 🔧 Se ha añadido el argumento de esquema
song_artists_table = Table(
    "song_artists",
    Base.metadata,
    Column(
        "song_id",
        Integer,
        # 🔧 Se ha actualizado la clave foránea para incluir el esquema
        ForeignKey("music_streaming.songs.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "artist_id",
        Integer,
        # 🔧 Se ha actualizado la clave foránea para incluir el esquema
        ForeignKey("music_streaming.artists.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Index("ix_song_artists_song_id_artist_id", "song_id", "artist_id", unique=True),
    # 🔧 Se ha añadido el esquema a la tabla
    schema="music_streaming",
)


class Artist(Base):
    __tablename__ = "artists"
    # 🔧 Se ha añadido el argumento de esquema
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(unique=True, index=True)
    artist_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    bio: Mapped[str | None] = mapped_column(Text)
    profile_pic: Mapped[str | None] = mapped_column(String)
    social_links: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    albums: Mapped[list["Album"]] = relationship(back_populates="artist", lazy="select")
    songs: Mapped[list["Song"]] = relationship(
        secondary=song_artists_table, back_populates="artists", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Artist id={self.id} user_id={self.user_id}>"


class Album(Base):
    __tablename__ = "albums"
    # 🔧 Se ha añadido el argumento de esquema
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    artist_id: Mapped[int] = mapped_column(
        # 🔧 Se ha actualizado la clave foránea para incluir el esquema
        ForeignKey("music_streaming.artists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String, nullable=False, index=True)
    release_date: Mapped[datetime.date | None] = mapped_column(Date)

    cover_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    artist: Mapped["Artist"] = relationship(back_populates="albums", lazy="joined")
    songs: Mapped[list["Song"]] = relationship(
        back_populates="album", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Album id={self.id} title={self.title} artist_id={self.artist_id}>"


class Genre(Base):
    __tablename__ = "genres"
    # 🔧 Se ha añadido el argumento de esquema
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    songs: Mapped[list["Song"]] = relationship(back_populates="genre", lazy="select")

    def __repr__(self) -> str:
        return f"<Genre id={self.id} name={self.name}>"


class Song(Base):
    __tablename__ = "songs"
    # 🔧 Se ha añadido el argumento de esquema
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    album_id: Mapped[int] = mapped_column(
        # 🔧 Se ha actualizado la clave foránea para incluir el esquema
        ForeignKey("music_streaming.albums.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    genre_id: Mapped[int] = mapped_column(
        # 🔧 Se ha actualizado la clave foránea para incluir el esquema
        ForeignKey("music_streaming.genres.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String, nullable=False, index=True)
    duration: Mapped[int | None]  # segundos
    audio_url: Mapped[str | None] = mapped_column(Text)
    track_number: Mapped[int | None]

    created_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    album: Mapped["Album"] = relationship(back_populates="songs", lazy="joined")
    genre: Mapped["Genre"] = relationship(back_populates="songs", lazy="joined")
    artists: Mapped[list["Artist"]] = relationship(
        secondary=song_artists_table, back_populates="songs", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Song id={self.id} title={self.title} album_id={self.album_id}>"
