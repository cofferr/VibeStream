from fastapi import HTTPException, status
from core.services.artist_lookup import ArtistLookupService


async def validate_song_ownership(song_repo, song_id: int, user_id: int, db):
    """Valida que el usuario autenticado sea propietario de la canción"""
    # Obtener el artist_id del usuario autenticado
    requester_artist_id = await ArtistLookupService.get_artist_id_by_user(user_id, db)
    print(f"DEBUG - User ID: {user_id}, Artist ID encontrado: {requester_artist_id}")

    if requester_artist_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está registrado como artista",
        )

    # Obtener el artist_id de la canción
    owner_artist_id = await song_repo.get_artist_id_by_song(song_id)
    print(f"DEBUG - Song ID: {song_id}, Owner Artist ID: {owner_artist_id}")

    if owner_artist_id != requester_artist_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar esta canción",
        )


async def validate_album_ownership(album_repo, album_id: int, user_id: int, db):
    """Valida que el usuario autenticado sea propietario del álbum"""
    # Obtener el artist_id del usuario autenticado
    requester_artist_id = await ArtistLookupService.get_artist_id_by_user(user_id, db)
    print(f"DEBUG - User ID: {user_id}, Artist ID encontrado: {requester_artist_id}")

    if requester_artist_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está registrado como artista",
        )

    # Obtener el artist_id del álbum
    owner_artist_id = await album_repo.get_artist_id_by_album(album_id)
    print(f"DEBUG - Album ID: {album_id}, Owner Artist ID: {owner_artist_id}")

    if owner_artist_id != requester_artist_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar este álbum",
        )
