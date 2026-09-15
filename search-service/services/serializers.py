# services/serializers.py
"""Serializadores para SearchIndexEntry (índice local, Fase 3/4).

Antes serializaban objetos ORM Song/Album/Artist con relaciones anidadas
cargadas desde la BD compartida; ahora todo viene de una sola fila
desnormalizada del índice local."""

import logging

logger = logging.getLogger(__name__)


def serialize_song(entry) -> dict | None:
    if not entry:
        return None
    try:
        return {
            "id": entry.entity_id,
            "title": entry.title,
            "duration": entry.duration,
            "audio_url": entry.audio_url,
            "track_number": entry.track_number,
            "album_id": entry.album_id,
            "artist_id": entry.artist_id,
            "artist_name": entry.subtitle,
            "updated_at": entry.updated_at,
        }
    except Exception:
        logger.exception("Error serializando canción del índice (id=%s)", getattr(entry, "entity_id", "unknown"))
        return None


def serialize_album(entry) -> dict | None:
    if not entry:
        return None
    try:
        return {
            "id": entry.entity_id,
            "title": entry.title,
            "cover_url": entry.cover_url,
            "artist_id": entry.artist_id,
            "artist_name": entry.subtitle,
            "updated_at": entry.updated_at,
        }
    except Exception:
        logger.exception("Error serializando álbum del índice (id=%s)", getattr(entry, "entity_id", "unknown"))
        return None


def serialize_artist(entry) -> dict | None:
    if not entry:
        return None
    try:
        return {
            "id": entry.entity_id,
            "name": entry.title,
            "profile_pic": entry.cover_url,
            "updated_at": entry.updated_at,
        }
    except Exception:
        logger.exception("Error serializando artista del índice (id=%s)", getattr(entry, "entity_id", "unknown"))
        return None
