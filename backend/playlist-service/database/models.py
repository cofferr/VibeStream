# database/models.py
"""playlist-service es dueño exclusivo de playlists/playlist_songs
(Fase 3). user_id y song_id ya no son FK locales: users vive en
auth-service y songs en content-service. playlist_songs guarda solo el
song_id; el enriquecimiento (título, artista, portada) se resuelve vía el
endpoint batch de content-service en vez de un join SQL local — es el
trade-off estándar de microservicios: se cambia un join gratis por una
llamada de red, a cambio de que cada servicio sea dueño real de su
esquema.

Columnas alineadas con create_database.sql (schema original real,
aportado por el usuario 2026-09-21): created_at/updated_at pasan de
DATE a TIMESTAMP (decisión explícita del usuario, diverge a propósito
del original) y se agregan las columnas de playlists que create_database.sql
sí tenía y acá faltaban (cover_image, is_public, is_collaborative,
total_songs, total_duration, follower_count, play_count, deleted_at).

playlist_songs no existe en el music_streaming real (solo en music_stm,
la versión legacy) — es una tabla que este servicio necesita igual para
que la feature funcione. added_by/position se tomaron de la tabla
equivalente de music_stm (playlists_canciones: agregado_por, orden),
que sí resolvía esto en el diseño legacy.

follower_count y play_count quedan como columnas con default 0 sin
lógica que las actualice (necesitarían "seguir playlist" y tracking de
reproducciones — deuda adyacente a analítica, explícitamente fuera de
alcance). deleted_at igual: la columna existe pero delete_playlist
sigue siendo borrado físico por ahora — cambiar la semántica de
"borrar" es una decisión aparte, no implícita en agregar la columna."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from vibestream_common.db import Base


class Playlist(Base):
    __tablename__ = "playlists"
    __table_args__ = {"schema": "music_streaming"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    cover_image: Mapped[Optional[str]] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_collaborative: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    total_songs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_duration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # sin lógica que los actualice todavía, ver docstring del módulo
    follower_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    play_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class PlaylistSong(Base):
    __tablename__ = "playlist_songs"
    __table_args__ = {"schema": "music_streaming"}

    playlist_id: Mapped[int] = mapped_column(
        ForeignKey("music_streaming.playlists.id"), primary_key=True
    )
    song_id: Mapped[int] = mapped_column(primary_key=True)
    # quién la agregó (relevante en playlists colaborativas); no es FK a
    # users (vive en auth-service, Fase 3)
    added_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # orden dentro de la playlist; nullable porque las filas existentes
    # antes de este cambio no tienen posición asignada
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # snapshot de la duración al momento de agregar la canción (no viene de
    # create_database.sql, es necesario para mantener Playlist.total_duration
    # sin un round-trip extra a content-service al quitar una canción, y sin
    # que quede desactualizado si la canción cambia de duración después)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
