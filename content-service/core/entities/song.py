from pydantic import BaseModel, field_validator
from datetime import date
from typing import Optional, List

from .artist import ArtistOut  # forward refs


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
    created_at: Optional[date]
    updated_at: Optional[date]
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
    created_at: Optional[date]
    updated_at: Optional[date]

    class Config:
        from_attributes = True

    @classmethod
    def from_song(cls, song) -> "SongEnrichedOut":
        album = song.album
        artist = album.artist if album else None
        if not artist and song.artists:
            artist = song.artists[0]
        return cls(
            id=song.id,
            title=song.title,
            duration=song.duration,
            audio_url=song.audio_url,
            track_number=song.track_number,
            album_id=song.album_id,
            album_title=album.title if album else None,
            album_cover_url=album.cover_url if album else None,
            artist_id=artist.id if artist else None,
            artist_name=artist.artist_name if artist else None,
            genre_id=song.genre_id,
            created_at=song.created_at,
            updated_at=song.updated_at,
        )
