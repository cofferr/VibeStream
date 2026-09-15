# album_handler.py
from fastapi import APIRouter, Depends, Request, File, UploadFile, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.db.connection import get_db
from core.repositories.album_repository import AlbumRepository
from core.services.album_service import AlbumService
from core.entities.album import AlbumOut, SongOut
from utils.json_response import success_response, error_response
from datetime import date
from typing import Optional
import logging

# 🔹 Importar validación de ownership
from utils.ownership import validate_album_ownership

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/albums", tags=["albums"])


# === Rutas "específicas" (literales) FIRST ===
@router.get("/my-albums", response_model=dict)
async def get_my_albums(request: Request, db: AsyncSession = Depends(get_db)):
    """Obtiene todos los álbumes del usuario autenticado con información completa"""
    # Verificar si el request.state.user existe
    if not hasattr(request.state, "user"):
        logger.warning("Solicitud a /my-albums sin request.state.user")
        return error_response(422, "Información de usuario no disponible en el request")

    user_id = request.state.user.get("user_id")
    if not user_id:
        logger.warning("Solicitud a /my-albums sin user_id en request.state.user")
        return error_response(422, "User ID no disponible en el request")

    service = AlbumService(AlbumRepository(db))

    try:
        # Usar ArtistLookupService para obtener el artist_id
        from core.services.artist_lookup import ArtistLookupService

        artist_id = await ArtistLookupService.get_artist_id_by_user(user_id, db)

        if not artist_id:
            return error_response(404, "No tienes un perfil de artista creado")

        # Obtener álbumes con información completa
        albums = await service.get_artist_albums_with_info(artist_id)

        return success_response(
            {"artist_id": artist_id, "total_albums": len(albums), "albums": albums},
            "Mis álbumes recuperados correctamente",
        )
    except Exception:
        logger.exception("Error al obtener mis álbumes (user_id=%s)", user_id)
        return error_response(500, "Error al obtener mis álbumes")


@router.get("/artist/{artist_id}", response_model=dict)
async def get_artist_albums(artist_id: int, db: AsyncSession = Depends(get_db)):
    """Obtiene todos los álbumes de un artista con información completa"""
    service = AlbumService(AlbumRepository(db))

    try:
        albums = await service.get_artist_albums_with_info(artist_id)

        return success_response(
            {"artist_id": artist_id, "total_albums": len(albums), "albums": albums},
            "Álbumes del artista recuperados correctamente",
        )
    except Exception:
        logger.exception("Error al obtener álbumes del artista %s", artist_id)
        return error_response(500, "Error al obtener álbumes")


# === Rutas con parámetro (más genéricas) después ===
@router.post("/", response_model=dict)
async def create_album(
    request: Request,
    db: AsyncSession = Depends(get_db),
    title: str = Form(...),
    release_date: Optional[str] = Form(None),
    cover_image: Optional[UploadFile] = File(None),
):
    user_id = request.state.user["user_id"]

    # Validar imagen si se proporciona
    if cover_image:
        if not cover_image.content_type or not cover_image.content_type.startswith(
            "image/"
        ):
            raise HTTPException(
                status_code=400, detail="El archivo debe ser una imagen válida"
            )

        if not cover_image.filename or not cover_image.filename.lower().endswith(
            (".png", ".jpg", ".jpeg")
        ):
            raise HTTPException(
                status_code=400, detail="Solo se permiten archivos PNG, JPG o JPEG"
            )

    # Procesar fecha
    parsed_date = None
    if release_date:
        try:
            parsed_date = date.fromisoformat(release_date)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD"
            )

    cover_data = await cover_image.read() if cover_image else None
    cover_filename = cover_image.filename if cover_image else None

    service = AlbumService(AlbumRepository(db))
    album = await service.create_album(
        title=title,
        user_id=user_id,
        db=db,
        release_date=parsed_date,
        cover_image=cover_data,
        cover_filename=cover_filename,
    )

    schema = AlbumOut.model_validate(album)
    return success_response(schema.model_dump(), "Álbum creado exitosamente")


@router.get("/{album_id}", response_model=dict)
async def get_album(album_id: int, db: AsyncSession = Depends(get_db)):
    """Devuelve un 404 HTTP real (no un 200 con {"status": "error"}) porque
    también la consume el consumer de search-service para distinguir
    "álbum no existe" de un error de red."""
    service = AlbumService(AlbumRepository(db))
    album = await service.get_album(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Álbum no encontrado")
    schema = AlbumOut.model_validate(album)
    return success_response(schema.model_dump(), "Álbum recuperado correctamente")


@router.get("/{album_id}/songs", response_model=dict)
async def list_album_songs(album_id: int, db: AsyncSession = Depends(get_db)):
    service = AlbumService(AlbumRepository(db))
    album = await service.get_album(album_id)
    if not album:
        return error_response(404, "Álbum no encontrado")

    songs = await service.list_songs_by_album(album_id)
    songs_schema = [SongOut.model_validate(song).model_dump() for song in songs]

    return success_response(
        {"songs": songs_schema}, "Canciones del álbum recuperadas correctamente"
    )


@router.put("/{album_id}", response_model=dict)
async def update_album(
    request: Request,
    album_id: int,
    db: AsyncSession = Depends(get_db),
    title: Optional[str] = Form(None),
    release_date: Optional[str] = Form(None),
    cover_image: Optional[UploadFile] = File(None),
):
    user_id = request.state.user["user_id"]

    # 🔹 Validar propiedad del álbum
    await validate_album_ownership(AlbumRepository(db), album_id, user_id, db)

    if cover_image:
        if not cover_image.content_type or not cover_image.content_type.startswith(
            "image/"
        ):
            raise HTTPException(
                status_code=400, detail="El archivo debe ser una imagen válida"
            )

        if not cover_image.filename or not cover_image.filename.lower().endswith(
            (".png", ".jpg", ".jpeg")
        ):
            raise HTTPException(
                status_code=400, detail="Solo se permiten archivos PNG, JPG o JPEG"
            )

    parsed_date = None
    if release_date:
        try:
            parsed_date = date.fromisoformat(release_date)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD"
            )

    service = AlbumService(AlbumRepository(db))
    album = await service.get_album(album_id)
    if not album:
        return error_response(404, "Álbum no encontrado")

    cover_data = await cover_image.read() if cover_image else None
    cover_filename = cover_image.filename if cover_image else None

    updated = await service.update_album(
        album, title=title, release_date=parsed_date, cover_image=cover_data, cover_filename=cover_filename
    )

    schema = AlbumOut.model_validate(updated)
    return success_response(schema.model_dump(), "Álbum actualizado correctamente")


@router.delete("/artist/{artist_id}", response_model=dict)
async def delete_albums_by_artist(artist_id: int, db: AsyncSession = Depends(get_db)):
    """Endpoint interno: borra todos los álbumes/canciones de un artista.
    Lo llama artist-service al eliminar la cuenta de un artista (Fase 3:
    ya no tiene acceso directo a estas tablas). Un 500 HTTP real es
    importante aquí: si el cascade falla, artist-service debe abortar el
    borrado del artista en vez de dejarlo huérfano de su contenido."""
    service = AlbumService(AlbumRepository(db))
    try:
        await service.delete_albums_by_artist(artist_id)
        return success_response({}, "Álbumes del artista eliminados correctamente")
    except Exception as e:
        logger.exception("Error eliminando álbumes del artista %s", artist_id)
        raise HTTPException(
            status_code=500, detail="Error al eliminar álbumes del artista"
        ) from e


@router.delete("/{album_id}", response_model=dict)
async def delete_album(request: Request, album_id: int, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user["user_id"]

    # 🔹 Validar propiedad del álbum
    await validate_album_ownership(AlbumRepository(db), album_id, user_id, db)

    service = AlbumService(AlbumRepository(db))
    album = await service.get_album(album_id)
    if not album:
        return error_response(404, "Álbum no encontrado")

    # 🔹 Esto elimina canciones + álbum
    await service.delete_album(album)

    return success_response({}, "Álbum eliminado correctamente")
