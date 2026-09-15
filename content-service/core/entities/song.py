from pydantic import BaseModel
from datetime import date
from typing import Optional, List

from .artist import ArtistOut  # forward refs


class SongBase(BaseModel):
    title: str
    duration: int
    audio_url: str
    track_number: Optional[int] = None


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
