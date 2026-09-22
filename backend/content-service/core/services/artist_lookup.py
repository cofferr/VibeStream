import logging

from sqlalchemy.ext.asyncio import AsyncSession
from vibestream_common.http_client import InternalHTTPClient, InternalServiceError

from config import settings

logger = logging.getLogger(__name__)

artist_client = InternalHTTPClient(settings.artist_service_url)


class ArtistLookupService:
    @staticmethod
    async def get_artist_id_by_user(user_id: int, db: AsyncSession):
        """Obtiene el artist_id basado en el user_id, vía HTTP a
        artist-service (Fase 6: antes hacía un select local contra una
        copia duplicada de Artist en content-service — ver
        infrastructure/db/models.py, ya eliminada). El parámetro `db` ya
        no se usa acá, se mantiene por compatibilidad con los ~7 call
        sites existentes en vez de tocarlos todos para este refactor.

        Retorna None si no se encuentra el artista o si artist-service no
        responde (mismo comportamiento que antes: un None se traduce en
        "el usuario no está registrado como artista" en utils/ownership.py,
        no en un 500).
        """
        try:
            response = await artist_client.get(f"/artists/by-user/{user_id}")
        except InternalServiceError:
            logger.exception(
                "No se pudo resolver artist_id para user_id %s vía artist-service",
                user_id,
            )
            return None

        artist = (response or {}).get("data")
        return artist.get("id") if artist else None

    @staticmethod
    async def get_artist_name(artist_id: int) -> str | None:
        """Resuelve el nombre de un artista por id, vía HTTP (Fase 6: usado
        para enriquecer SongEnrichedOut, antes resuelto con un join local a
        una copia duplicada de Artist en content-service)."""
        try:
            response = await artist_client.get(f"/artists/{artist_id}")
        except InternalServiceError:
            logger.exception(
                "No se pudo resolver artist_name para artist_id %s", artist_id
            )
            return None

        artist = (response or {}).get("data")
        return artist.get("artist_name") if artist else None
