from typing import List

from vibestream_common.http_client import InternalHTTPClient, InternalServiceError

from config import settings
from repositories.repository import SubscriptionRepository


class SubscriptionService:
    def __init__(self, repository: SubscriptionRepository):
        self.repository = repository
        self.artist_client = InternalHTTPClient(settings.artist_service_url)

    async def subscribe(self, user_id: int, artist_id: int):
        if user_id == artist_id:
            raise ValueError("No puedes suscribirte a ti mismo.")
        if await self.repository.exists(user_id, artist_id):
            raise ValueError("Ya estás suscrito a este artista.")

        artist = await self._get_artist_or_none(artist_id)
        if artist is None:
            raise ValueError("El artista no existe.")

        return await self.repository.add(user_id, artist_id)

    async def _get_artist_or_none(self, artist_id: int) -> dict | None:
        try:
            response = await self.artist_client.get(f"/artists/{artist_id}")
        except InternalServiceError:
            raise ValueError("No se pudo validar el artista, intenta de nuevo.")
        if not response:
            return None
        return response.get("data")

    async def unsubscribe(self, user_id: int, artist_id: int):
        if not await self.repository.exists(user_id, artist_id):
            raise ValueError("No existe suscripción para eliminar.")
        await self.repository.remove(user_id, artist_id)

    # 🔹 NUEVOS MÉTODOS
    async def get_user_subscriptions_enriched(self, user_id: int) -> List[dict]:
        """Obtiene las suscripciones de un usuario con el nombre del artista
        resuelto vía HTTP (antes era un join local a artists)."""
        subscriptions = await self.repository.get_user_subscriptions(user_id)

        enriched = []
        for sub in subscriptions:
            artist = await self._get_artist_or_none(sub.artist_id)
            enriched.append(
                {
                    "artist_id": sub.artist_id,
                    "artist_name": artist.get("artist_name") if artist else None,
                    "created_at": sub.created_at,
                }
            )
        return enriched

    async def get_user_subscribed_artists(self, user_id: int) -> List[int]:
        """Obtiene solo los IDs de los artistas a los que está suscrito un usuario"""
        return await self.repository.get_user_subscribed_artists(user_id)

    async def get_subscription_count(self, user_id: int) -> int:
        """Obtiene el número total de suscripciones de un usuario"""
        subscriptions = await self.repository.get_user_subscriptions(user_id)
        return len(subscriptions)
