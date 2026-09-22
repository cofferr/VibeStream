"""search-service es dueño exclusivo de search_index (Fase 3/4).

Ya no lee songs/albums/artists directo de la BD compartida: mantiene un
índice local desnormalizado, alimentado por eventos RabbitMQ publicados por
content-service (song_created/updated, album_created/updated) y
artist-service (artist_created/updated). Es el patrón CQRS correcto para
búsqueda difusa con rapidfuzz — evitar N llamadas HTTP síncronas por cada
búsqueda, que serían demasiado lentas."""

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint, func

from database.connection import Base


class SearchIndexEntry(Base):
    __tablename__ = "search_index"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", name="uq_search_index_entity"),
        {"schema": "music_streaming"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False, index=True)  # "song" | "album" | "artist"
    entity_id = Column(Integer, nullable=False, index=True)

    title = Column(String, nullable=False, index=True)
    subtitle = Column(String, nullable=True)  # artista de la canción/álbum
    cover_url = Column(Text, nullable=True)
    audio_url = Column(Text, nullable=True)

    artist_id = Column(Integer, nullable=True, index=True)
    album_id = Column(Integer, nullable=True, index=True)
    duration = Column(Integer, nullable=True)
    track_number = Column(Integer, nullable=True)

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
