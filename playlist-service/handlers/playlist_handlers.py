# handlers/playlist_handlers.py
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import Playlist
from errors import handle_errors
from repositories.playlist_repository import PlaylistRepository
from services.playlist_service import PlaylistService

logger = logging.getLogger(__name__)

router = APIRouter()


# DTOs para JSON
class CreatePlaylistRequest(BaseModel):
    name: str
    description: Optional[str] = None


class UpdatePlaylistRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class AddSongRequest(BaseModel):
    song_id: int


def _playlist_to_dict(playlist: Playlist) -> dict:
    """Convierte un objeto Playlist a diccionario para la respuesta"""
    return {
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "user_id": playlist.user_id,
        "created_at": playlist.created_at,
        "updated_at": playlist.updated_at,
    }


@router.post("/", response_model=dict)
@handle_errors
async def create_playlist(
    request: Request,
    playlist_data: CreatePlaylistRequest,
    db: AsyncSession = Depends(get_db),
):
    """Crear una nueva playlist"""
    if not hasattr(request.state, "user"):
        logger.error("request.state.user no existe - problema con AuthMiddleware")
        raise HTTPException(
            status_code=401, detail="No se encontró información de usuario"
        )

    user_id = request.state.user["user_id"]

    repo = PlaylistRepository(db)
    service = PlaylistService(repo, user_id)

    playlist = await service.create_playlist(
        playlist_data.name, playlist_data.description
    )

    return _playlist_to_dict(playlist)


@router.get("/{playlist_id}", response_model=dict)
@handle_errors
async def get_playlist(
    request: Request,
    playlist_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Obtener una playlist por ID"""
    user_id = request.state.user["user_id"]

    repo = PlaylistRepository(db)
    service = PlaylistService(repo, user_id)
    playlist = await service.get_playlist(playlist_id)

    if playlist is None:
        raise HTTPException(
            status_code=404,
            detail="Playlist no encontrada o no tienes permisos para acceder",
        )

    return _playlist_to_dict(playlist)


@router.put("/{playlist_id}", response_model=dict)
@handle_errors
async def update_playlist(
    request: Request,
    playlist_id: int,
    playlist_data: UpdatePlaylistRequest,
    db: AsyncSession = Depends(get_db),
):
    """Actualizar una playlist existente"""
    user_id = request.state.user["user_id"]

    # Validar que al menos un campo se esté actualizando
    if playlist_data.name is None and playlist_data.description is None:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar al menos un campo para actualizar",
        )

    repo = PlaylistRepository(db)
    service = PlaylistService(repo, user_id)
    playlist = await service.update_playlist(
        playlist_id, playlist_data.name, playlist_data.description
    )

    if playlist is None:
        raise HTTPException(
            status_code=404,
            detail="Playlist no encontrada o no tienes permisos para modificarla",
        )

    return _playlist_to_dict(playlist)


@router.delete("/{playlist_id}", response_model=dict)
@handle_errors
async def delete_playlist(
    request: Request, playlist_id: int, db: AsyncSession = Depends(get_db)
):
    """Eliminar una playlist"""
    user_id = request.state.user["user_id"]

    repo = PlaylistRepository(db)
    service = PlaylistService(repo, user_id)
    deleted = await service.delete_playlist(playlist_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Playlist no encontrada o no tienes permisos para eliminarla",
        )

    return {
        "message": "Playlist eliminada correctamente",
        "playlist_id": playlist_id,
    }


@router.get("/{playlist_id}/songs", response_model=dict)
@handle_errors
async def get_playlist_songs(
    request: Request,
    playlist_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Obtener todas las canciones de una playlist"""
    user_id = request.state.user["user_id"]

    repo = PlaylistRepository(db)
    service = PlaylistService(repo, user_id)

    # Primero verificamos si la playlist existe
    playlist = await service.get_playlist(playlist_id)
    if playlist is None:
        raise HTTPException(
            status_code=404,
            detail="Playlist no encontrada o no tienes permisos para acceder a ella",
        )

    # Obtener las canciones
    songs = await service.get_playlist_songs(playlist_id)

    return {"playlist_id": playlist_id, "songs_count": len(songs), "songs": songs}


@router.post("/{playlist_id}/songs", response_model=dict)
@handle_errors
async def add_song_to_playlist(
    request: Request,
    playlist_id: int,
    song_data: AddSongRequest,
    db: AsyncSession = Depends(get_db),
):
    """Añadir una canción a la playlist"""
    user_id = request.state.user["user_id"]

    repo = PlaylistRepository(db)
    service = PlaylistService(repo, user_id)

    success, message = await service.add_song_to_playlist(
        playlist_id, song_data.song_id
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "message": message,
        "playlist_id": playlist_id,
        "song_id": song_data.song_id,
    }


@router.delete("/{playlist_id}/songs/{song_id}", response_model=dict)
@handle_errors
async def remove_song_from_playlist(
    request: Request,
    playlist_id: int,
    song_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Eliminar una canción de la playlist"""
    user_id = request.state.user["user_id"]

    repo = PlaylistRepository(db)
    service = PlaylistService(repo, user_id)

    success, message = await service.remove_song_from_playlist(playlist_id, song_id)

    if not success:
        raise HTTPException(status_code=404, detail=message)

    return {"message": message, "playlist_id": playlist_id, "song_id": song_id}


@router.get("/", response_model=dict)
@handle_errors
async def get_user_playlists(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    Obtener todas las playlists del usuario autenticado

    Query Parameters:
        page: Número de página (default: 1)
        page_size: Elementos por página (default: 20, max: 100)

    Returns:
        {
            "playlists": [
                {
                    "id": int,
                    "name": str,
                    "description": str,
                    "user_id": int,
                    "created_at": date,
                    "updated_at": date
                }
            ],
            "pagination": {
                "current_page": int,
                "page_size": int,
                "total_items": int,
                "total_pages": int,
                "has_next": bool,
                "has_previous": bool
            },
            "summary": {
                "total_playlists": int,
                "showing": int
            }
        }
    """
    user_id = request.state.user["user_id"]

    repo = PlaylistRepository(db)
    service = PlaylistService(repo, user_id)

    return await service.get_user_playlists(page, page_size)
