import datetime

from sqlalchemy import (
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


# Tabla de asociación many-to-many entre songs y artists. artist_id NO
# tiene FK física a music_streaming.artists (Fase 6): esa tabla es de
# artist-service, no de content-service, y una FK física cross-schema es
# justo lo que Fase 3 buscaba eliminar. Se valida la existencia del
# artista vía HTTP en SongService.create_song antes de insertar acá.
song_artists_table = Table(
    "song_artists",
    Base.metadata,
    Column(
        "song_id",
        Integer,
        ForeignKey("music_streaming.songs.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("artist_id", Integer, primary_key=True),
    Index("ix_song_artists_song_id_artist_id", "song_id", "artist_id", unique=True),
    schema="music_streaming",
)


class Album(Base):
    __tablename__ = "albums"
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Sin FK física a music_streaming.artists (Fase 6, mismo razonamiento
    # que song_artists_table de arriba). Se resuelve/valida vía HTTP a
    # artist-service (ArtistLookupService) antes de crear el álbum.
    artist_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False, index=True)
    release_date: Mapped[datetime.date | None] = mapped_column(Date)

    cover_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    songs: Mapped[list["Song"]] = relationship(
        back_populates="album", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Album id={self.id} title={self.title} artist_id={self.artist_id}>"


class Genre(Base):
    __tablename__ = "genres"
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    songs: Mapped[list["Song"]] = relationship(back_populates="genre", lazy="select")

    def __repr__(self) -> str:
        return f"<Genre id={self.id} name={self.name}>"


class Song(Base):
    __tablename__ = "songs"
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    album_id: Mapped[int] = mapped_column(
        ForeignKey("music_streaming.albums.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    genre_id: Mapped[int] = mapped_column(
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

    def __repr__(self) -> str:
        return f"<Song id={self.id} title={self.title} album_id={self.album_id}>"
