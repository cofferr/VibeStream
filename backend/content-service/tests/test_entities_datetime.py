"""Regresión del bug real encontrado al verificar la Fase 3 con Docker:
AlbumOut/SongOut/SongEnrichedOut tipaban created_at/updated_at como
`date` cuando la columna real en Postgres es `timestamp`. Pydantic
rechazaba cualquier fila con hora != medianoche con
`date_from_datetime_inexact`, lo que rompía GET /albums/{id} y GET
/songs/{id}/enriched — los endpoints que search-service/playlist-service
usan para enriquecimiento HTTP (Fase 3)."""

from datetime import datetime

from core.entities.album import AlbumOut
from core.entities.song import SongEnrichedOut, SongOut

NOT_MIDNIGHT = datetime(2026, 9, 15, 20, 27, 12, 772047)


def test_album_out_accepts_real_timestamp():
    album = AlbumOut(
        id=1,
        artist_id=1,
        title="Sencillos",
        created_at=NOT_MIDNIGHT,
        updated_at=NOT_MIDNIGHT,
    )
    assert album.created_at == NOT_MIDNIGHT


def test_song_out_accepts_real_timestamp():
    song = SongOut(
        id=1,
        album_id=1,
        genre_id=None,
        title="Una Canción",
        duration=180,
        audio_url="https://example.com/song.mp3",
        created_at=NOT_MIDNIGHT,
        updated_at=NOT_MIDNIGHT,
    )
    assert song.updated_at == NOT_MIDNIGHT


def test_song_enriched_out_accepts_real_timestamp():
    song = SongEnrichedOut(
        id=1,
        album_id=1,
        genre_id=None,
        title="Una Canción",
        duration=180,
        audio_url="https://example.com/song.mp3",
        created_at=NOT_MIDNIGHT,
        updated_at=NOT_MIDNIGHT,
    )
    assert song.created_at == NOT_MIDNIGHT
