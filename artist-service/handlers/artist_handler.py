import json
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from models.artist import ArtistCreateSchema, ArtistUpdateSchema
from services.artist_service import ArtistService
from utils.json_response import error_response, success_response

router = APIRouter()


@router.post("/register", status_code=201, response_model=dict)
async def register_artist(
    request: Request,
    artist_name: str = Form(...),
    bio: Optional[str] = Form(None),
    social_links: Optional[str] = Form(None),  # se envía como string JSON
    profile_pic_file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    user_id = request.state.user["user_id"]

    # Logging para depuración
    print(f"📥 Registro de artista solicitado por user_id: {user_id}")
    print(f"🎨 artist_name: {artist_name}"
          f", bio: {bio}"
          f", social_links: {social_links}"
          f", profile_pic_file: {'Sí' if profile_pic_file else 'No'}")

    # Verificar si ya existe un artista
    existing_artist = await ArtistService.get_artist_by_user(db, user_id)
    if existing_artist:
        raise HTTPException(
            status_code=409,
            detail=error_response(
                409, "Ya existe un artista registrado para este usuario"
            ),
        )

    # Parsear social_links si viene como JSON string
    links_dict = None
    if social_links:
        try:
            links_dict = json.loads(social_links)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=error_response(400, "Formato inválido en social_links"),
            ) from e

    payload = ArtistCreateSchema(
        artist_name=artist_name,
        bio=bio,
        profile_pic=None,  # se setea luego si hay archivo
        social_links=links_dict,
    )

    artist = await ArtistService.register_artist(db, user_id, payload, profile_pic_file)

    return success_response(
        artist.model_dump(),
        "Artista registrado correctamente",
    )


@router.get("/me", response_model=dict)
async def get_my_artist(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user["user_id"]
    print(f"🔍 Buscando artista para user_id: {user_id}")

    artist = await ArtistService.get_artist_by_user(db, user_id)
    
    if not artist:
        print(f"ℹ️ Usuario {user_id} no es artista")
        return success_response(
            {"isArtist": False},
            "Usuario no es artista"
        )

    print(f"✅ Usuario {user_id} es artista")
    return success_response(
        {
            "isArtist": True,
            "artist": artist.model_dump()
        },
        "Perfil de artista obtenido"
    )


@router.put("/me", response_model=dict)
async def update_my_artist(
    request: Request,
    artist_name: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    social_links: Optional[str] = Form(None),
    profile_pic_file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    user_id = request.state.user["user_id"]

    # 🔧 Siempre inicializamos links_dict
    links_dict = None
    if social_links:
        try:
            links_dict = json.loads(social_links)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=error_response(400, "Formato inválido en social_links"),
            ) from e

    # 🔧 payload siempre definido
    payload = ArtistUpdateSchema(
        artist_name=artist_name,
        bio=bio,
        social_links=links_dict,
    )

    artist = await ArtistService.update_artist_by_user(
        db, user_id, payload, profile_pic_file
    )
    if not artist:
        raise HTTPException(status_code=404, detail="Artista no encontrado")

    return success_response(artist.model_dump(), "Artista actualizado correctamente")


@router.delete("/me", response_model=dict)
async def delete_my_artist(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user["user_id"]

    deleted = await ArtistService.delete_artist_by_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Artista no encontrado")

    return success_response({}, "Artista eliminado correctamente")


@router.get("/{artist_id}", response_model=dict)
async def get_artist_by_id(artist_id: int, db: AsyncSession = Depends(get_db)):
    """Endpoint público de lectura: content-service, search-service y
    subscription-service lo usan para resolver/validar datos de artista
    sin acceso directo a la tabla artists."""
    artist = await ArtistService.get_artist_by_id(db, artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="Artista no encontrado")

    return success_response(artist.model_dump(), "Artista recuperado correctamente")