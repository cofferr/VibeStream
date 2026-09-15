"""Cubre utils.ownership.validate_album_ownership: quién puede editar un
álbum ajeno es una decisión de autorización real, no solo un detalle de
implementación — vale la pena un test explícito en vez de confiar en
probarlo manualmente cada vez."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from utils.ownership import validate_album_ownership


class _FakeAlbumRepo:
    def __init__(self, owner_artist_id):
        self.owner_artist_id = owner_artist_id

    async def get_artist_id_by_album(self, album_id: int):
        return self.owner_artist_id


@patch(
    "utils.ownership.ArtistLookupService.get_artist_id_by_user",
    new_callable=AsyncMock,
)
async def test_owner_can_edit_own_album(mock_lookup):
    mock_lookup.return_value = 5  # el user autenticado es el artista 5
    repo = _FakeAlbumRepo(owner_artist_id=5)

    # no debe lanzar
    await validate_album_ownership(repo, album_id=1, user_id=42, db=None)


@patch(
    "utils.ownership.ArtistLookupService.get_artist_id_by_user",
    new_callable=AsyncMock,
)
async def test_non_owner_gets_403(mock_lookup):
    mock_lookup.return_value = 5  # el user autenticado es el artista 5
    repo = _FakeAlbumRepo(owner_artist_id=99)  # el álbum es de otro artista

    with pytest.raises(HTTPException) as exc_info:
        await validate_album_ownership(repo, album_id=1, user_id=42, db=None)

    assert exc_info.value.status_code == 403


@patch(
    "utils.ownership.ArtistLookupService.get_artist_id_by_user",
    new_callable=AsyncMock,
)
async def test_non_artist_user_gets_403(mock_lookup):
    mock_lookup.return_value = None  # el user no tiene perfil de artista
    repo = _FakeAlbumRepo(owner_artist_id=5)

    with pytest.raises(HTTPException) as exc_info:
        await validate_album_ownership(repo, album_id=1, user_id=42, db=None)

    assert exc_info.value.status_code == 403
