# song_handler.py
from fastapi import APIRouter, Depends, Request, File, UploadFile, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.db.connection import get_db
from core.repositories.song_repository import SongRepository
from core.repositories.album_repository import AlbumRepository
from core.services.song_service import SongService
from core.entities.song import SongOut
from utils.json_response import success_response, error_response
from typing import Optional
from utils.audio_validation import validate_audio_file
from utils.ownership import (
    validate_song_ownership,
    validate_album_ownership,
)  # 🔹 Importar validación de ownership

router = APIRouter(prefix="/songs", tags=["songs"])


@router.post("/", response_model=dict)
async def create_song(
    request: Request,  # obligatorio primero
    title: str = Form(...),
    album_id: int = Form(...),
    audio_file: UploadFile = File(...),
    track_number: Optional[int] = Form(None),
    genre_id: Optional[int] = Form(None),
    artist_ids: Optional[str] = Form(None),
    override_duration: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    user_id = request.state.user["user_id"]

    # 🔹 NUEVA VALIDACIÓN: Verificar que el álbum pertenezca al usuario
    await validate_album_ownership(AlbumRepository(db), album_id, user_id, db)

    # 🔹 Validar archivo de audio
    validate_audio_file(audio_file)

    # 🔹 Procesar artist_ids si se proporcionan
    parsed_artist_ids = None
    if artist_ids:
        try:
            parsed_artist_ids = [
                int(id.strip()) for id in artist_ids.split(",") if id.strip()
            ]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="artist_ids debe ser una lista de números separados por comas",
            )

    # 🔹 Obtener información del álbum (ya validado que pertenece al usuario)
    album_repo = AlbumRepository(db)
    album = await album_repo.get_by_id(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Álbum no encontrado")

    album_name = album.title  # (podría usarse para almacenamiento físico en carpeta)

    # 🔹 Leer datos del archivo de audio
    audio_data = await audio_file.read()

    # 🔹 Validar tamaño del archivo (opcional - máximo 50MB)
    max_size = 50 * 1024 * 1024  # 50MB
    if len(audio_data) > max_size:
        raise HTTPException(
            status_code=400,
            detail="El archivo de audio es demasiado grande (máximo 50MB)",
        )

    service = SongService(SongRepository(db))
    song = await service.create_song(
        title=title,
        album_id=album_id,
        user_id=user_id,
        audio_file=audio_data,
        audio_filename=audio_file.filename or "unknown.mp3",
        db=db,
        artist_ids=parsed_artist_ids,
        track_number=track_number,
        genre_id=genre_id,
        override_duration=override_duration,
    )

    schema = SongOut.model_validate(song)
    return success_response(schema.model_dump(), "Canción creada exitosamente")


@router.get("/{song_id}", response_model=dict)
async def get_song(song_id: int, db: AsyncSession = Depends(get_db)):
    service = SongService(SongRepository(db))
    song = await service.get_song(song_id)
    if not song:
        return error_response(404, "Canción no encontrada")
    schema = SongOut.model_validate(song)
    return success_response(schema.model_dump(), "Canción recuperada correctamente")


@router.put("/{song_id}", response_model=dict)
async def update_song(
    request: Request,
    song_id: int,
    title: Optional[str] = Form(None),
    track_number: Optional[int] = Form(None),
    genre_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    user_id = request.state.user["user_id"]

    # 🔹 Validar propiedad de la canción
    await validate_song_ownership(SongRepository(db), song_id, user_id, db)

    service = SongService(SongRepository(db))
    song = await service.get_song(song_id)
    if not song:
        return error_response(404, "Canción no encontrada")

    updated = await service.update_song(
        song,
        title=title,
        track_number=track_number,
        genre_id=genre_id,
    )

    schema = SongOut.model_validate(updated)
    return success_response(schema.model_dump(), "Canción actualizada correctamente")


@router.delete("/{song_id}", response_model=dict)
async def delete_song(
    request: Request, song_id: int, db: AsyncSession = Depends(get_db)
):
    user_id = request.state.user["user_id"]

    # 🔹 Validar propiedad de la canción
    await validate_song_ownership(SongRepository(db), song_id, user_id, db)

    service = SongService(SongRepository(db))
    song = await service.get_song(song_id)
    if not song:
        return error_response(404, "Canción no encontrada")

    await service.delete_song(song)
    return success_response({}, "Canción eliminada correctamente")
