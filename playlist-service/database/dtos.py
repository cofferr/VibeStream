from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import date


# DTOs para requests
class CreatePlaylistRequest(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=255, description="Nombre de la playlist"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Descripción de la playlist"
    )


class UpdatePlaylistRequest(BaseModel):
    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Nuevo nombre de la playlist"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Nueva descripción de la playlist"
    )


class AddSongRequest(BaseModel):
    song_id: int = Field(..., gt=0, description="ID de la canción a añadir")


# DTOs para responses
class SongResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    duration: Optional[int]
    audio_url: str
    track_number: Optional[int]
    album_id: int
    genre_id: int
    added_at: date


class PlaylistMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    description: Optional[str]
    created_at: date
    updated_at: date
    songs_count: int
    total_duration: Optional[int]  # Duración total en segundos


class PlaylistDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    description: Optional[str]
    created_at: date
    updated_at: date
    songs_count: int
    total_duration: Optional[int]
    songs: List[SongResponse]


class PlaylistListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    playlists: List[PlaylistMetadataResponse]
    total: int
    page: int
    page_size: int
