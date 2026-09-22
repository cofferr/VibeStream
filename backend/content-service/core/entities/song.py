from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator


class SongBase(BaseModel):
    title: str
    duration: int
    audio_url: str
    track_number: Optional[int] = None


class SongCreateFormData(BaseModel):
    """Valida los campos de metadata recibidos como multipart/form-data
    en POST /songs (el archivo de audio en sí no puede validarse vía
    Pydantic porque FastAPI no permite mezclar UploadFile con un body
    JSON en el mismo endpoint)."""

    title: str
    album_id: int
    track_number: Optional[int] = None
    genre_id: Optional[int] = None
    artist_ids: Optional[List[int]] = None
    override_duration: Optional[int] = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title no puede estar vacío")
        return v.strip()

    @field_validator("track_number", "override_duration")
    @classmethod
    def positive_if_present(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("debe ser un número positivo")
        return v


class SongCreate(SongBase):
    album_id: int
    genre_id: Optional[int] = None
    artist_ids: List[int]  # para la relación many-to-many


class SongUpdate(SongBase):
    album_id: Optional[int] = None
    genre_id: Optional[int] = None


class SongOut(SongBase):
    id: int
    album_id: int
    genre_id: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    # artists: List["ArtistOut"] = []

    class Config:
        from_attributes = True


class SongEnrichedOut(SongBase):
    """Vista de canción con álbum y artista ya resueltos, para servicios
    que consumen esta API en vez de leer la tabla songs directamente
    (playlist-service, search-service)."""

    id: int
    album_id: int
    album_title: Optional[str] = None
    album_cover_url: Optional[str] = None
    artist_id: Optional[int] = None
    artist_name: Optional[str] = None
    genre_id: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

    @classmethod
    def from_song(cls, song, artist_name: Optional[str] = None) -> "SongEnrichedOut":
        """artist_name se resuelve vía HTTP a artist-service en el caller
        (core/services/artist_lookup.py: get_artist_name) — Fase 6: antes
        se leía de song.album.artist / song.artists, una copia local
        duplicada de la tabla de artist-service que content-service ya no
        mantiene."""
        album = song.album
        return cls(
            id=song.id,
            title=song.title,
            duration=song.duration,
            audio_url=song.audio_url,
            track_number=song.track_number,
            album_id=song.album_id,
            album_title=album.title if album else None,
            album_cover_url=album.cover_url if album else None,
            artist_id=album.artist_id if album else None,
            artist_name=artist_name,
            genre_id=song.genre_id,
            created_at=song.created_at,
            updated_at=song.updated_at,
        )
