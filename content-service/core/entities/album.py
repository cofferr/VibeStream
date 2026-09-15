from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class AlbumBase(BaseModel):
    title: str
    release_date: Optional[date] = None
    cover_url: Optional[str] = None


class AlbumCreate(AlbumBase):
    artist_id: int  # viene del claim o request


class AlbumUpdate(AlbumBase):
    pass


class AlbumOut(AlbumBase):
    id: int
    artist_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    # songs: List["SongOut"] = []  # quitar

    class Config:
        from_attributes = True
