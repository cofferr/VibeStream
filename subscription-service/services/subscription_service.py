from typing import List
from repositories.repository import SubscriptionRepository
from database.models import ArtistSubscription


class SubscriptionService:
    def __init__(self, repository: SubscriptionRepository):
        self.repository = repository

    async def subscribe(self, user_id: int, artist_id: int):
        if user_id == artist_id:
            raise ValueError("No puedes suscribirte a ti mismo.")
        if await self.repository.exists(user_id, artist_id):
            raise ValueError("Ya estás suscrito a este artista.")
        return await self.repository.add(user_id, artist_id)

    async def unsubscribe(self, user_id: int, artist_id: int):
        if not await self.repository.exists(user_id, artist_id):
            raise ValueError("No existe suscripción para eliminar.")
        await self.repository.remove(user_id, artist_id)

    # 🔹 NUEVOS MÉTODOS
    async def get_user_subscriptions(self, user_id: int) -> List[ArtistSubscription]:
        """Obtiene todas las suscripciones de un usuario con información completa"""
        return await self.repository.get_user_subscriptions(user_id)

    async def get_user_subscribed_artists(self, user_id: int) -> List[int]:
        """Obtiene solo los IDs de los artistas a los que está suscrito un usuario"""
        return await self.repository.get_user_subscribed_artists(user_id)

    async def get_subscription_count(self, user_id: int) -> int:
        """Obtiene el número total de suscripciones de un usuario"""
        subscriptions = await self.repository.get_user_subscriptions(user_id)
        return len(subscriptions)
