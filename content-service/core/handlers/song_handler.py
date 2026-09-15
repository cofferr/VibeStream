# song_handler.py
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.song import SongCreateFormData, SongEnrichedOut, SongOut
from core.repositories.album_repository import AlbumRepository
from core.repositories.song_repository import SongRepository
from core.services.song_service import SongService
from infrastructure.db.connection import get_db
from utils.audio_validation import validate_audio_file
from utils.json_response import error_response, success_response
from utils.ownership import (
    validate_album_ownership,
    validate_song_ownership,
)  # 🔹 Importar validación de ownership

router = APIRouter(prefix="/songs", tags=["songs"])


# === Rutas "específicas" (literales) van ANTES de /{song_id} ===
@router.get("/batch", response_model=dict)
async def get_songs_batch(
    ids: str = Query(..., description="IDs de canciones separados por comas"),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint público de lectura: resuelve un lote de song_ids con álbum
    y artista ya enriquecidos. Usado por playlist-service (sus playlists
    solo guardan song_id) y por search-service para evitar N llamadas."""
    try:
        song_ids = [int(i.strip()) for i in ids.split(",") if i.strip()]
    except ValueError:
        raise HTTPException(
            status_code=400, detail="ids debe ser una lista de números separados por comas"
        )

    service = SongService(SongRepository(db))
    songs = await service.list_songs_with_info(song_ids)
    enriched = [SongEnrichedOut.from_song(song).model_dump() for song in songs]
    return success_response({"songs": enriched}, "Canciones recuperadas correctamente")


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

    # 🔹 Procesar artist_ids (lista separada por comas) antes de validar
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

    # 🔹 Validar los campos de metadata con Pydantic (el archivo en sí se
    # valida aparte porque FastAPI no permite mezclar UploadFile con un
    # body Pydantic en el mismo endpoint multipart)
    try:
        form_data = SongCreateFormData(
            title=title,
            album_id=album_id,
            track_number=track_number,
            genre_id=genre_id,
            artist_ids=parsed_artist_ids,
            override_duration=override_duration,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from e

    # 🔹 NUEVA VALIDACIÓN: Verificar que el álbum pertenezca al usuario
    await validate_album_ownership(AlbumRepository(db), form_data.album_id, user_id, db)

    # 🔹 Validar archivo de audio
    validate_audio_file(audio_file)

    # 🔹 Obtener información del álbum (ya validado que pertenece al usuario)
    album_repo = AlbumRepository(db)
    album = await album_repo.get_by_id(form_data.album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Álbum no encontrado")

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
        title=form_data.title,
        album_id=form_data.album_id,
        user_id=user_id,
        audio_file=audio_data,
        audio_filename=audio_file.filename or "unknown.mp3",
        db=db,
        artist_ids=form_data.artist_ids,
        track_number=form_data.track_number,
        genre_id=form_data.genre_id,
        override_duration=form_data.override_duration,
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


@router.get("/{song_id}/enriched", response_model=dict)
async def get_song_enriched(song_id: int, db: AsyncSession = Depends(get_db)):
    """Endpoint público de lectura con álbum/artista ya resueltos. Devuelve
    un 404 HTTP real (no un 200 con {"status": "error"}) porque lo llaman
    otros servicios (playlist-service, search-service) que necesitan
    distinguir "no existe" de "el body no cumplió el schema esperado"."""
    service = SongService(SongRepository(db))
    song = await service.get_song_with_info(song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    schema = SongEnrichedOut.from_song(song)
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
