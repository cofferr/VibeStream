from pydantic import BaseModel
from datetime import date
from typing import Optional, List

from .song import SongOut  # import circular controlado con forward refs


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
    created_at: Optional[date]
    updated_at: Optional[date]
    # songs: List["SongOut"] = []  # quitar

    class Config:
        from_attributes = True
