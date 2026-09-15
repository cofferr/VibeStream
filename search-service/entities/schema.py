from pydantic import BaseModel
from typing import Optional
from datetime import date


class UserOut(BaseModel):
    id: int
    name: Optional[str]
    username: str

    class Config:
        orm_mode = True


class ArtistOut(BaseModel):
    id: int
    bio: Optional[str]
    profile_pic: Optional[str]
    social_links: Optional[dict]
    created_at: Optional[date]
    updated_at: Optional[date]
    user: Optional[UserOut]

    class Config:
        orm_mode = True


class AlbumOut(BaseModel):
    id: int
    title: str
    release_date: Optional[date]
    cover_url: Optional[str]
    created_at: Optional[date]
    updated_at: Optional[date]
    artist: Optional[ArtistOut]

    class Config:
        orm_mode = True


class SongOut(BaseModel):
    id: int
    title: str
    duration: Optional[int]
    audio_url: str
    track_number: Optional[int]
    created_at: Optional[date]
    updated_at: Optional[date]
    album: Optional[AlbumOut]

    class Config:
        orm_mode = True
