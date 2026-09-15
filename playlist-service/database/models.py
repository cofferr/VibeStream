# database/models.py
"""playlist-service es dueño exclusivo de playlists/playlist_songs
(Fase 3). user_id y song_id ya no son FK locales: users vive en
auth-service y songs en content-service. playlist_songs guarda solo el
song_id; el enriquecimiento (título, artista, portada) se resuelve vía el
endpoint batch de content-service en vez de un join SQL local — es el
trade-off estándar de microservicios: se cambia un join gratis por una
llamada de red, a cambio de que cada servicio sea dueño real de su
esquema."""
from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from vibestream_common.db import Base


class Playlist(Base):
    __tablename__ = "playlists"
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
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
    song_id: Mapped[int] = mapped_column(primary_key=True)
    added_at: Mapped[date] = mapped_column(Date, server_default=func.current_date())
