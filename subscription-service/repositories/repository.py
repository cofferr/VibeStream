from datetime import date
from typing import List, Protocol

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ArtistSubscription


# 🔹 Contrato (interfaz) del repositorio
class SubscriptionRepository(Protocol):
    async def add(self, user_id: int, artist_id: int) -> ArtistSubscription: ...
    async def remove(self, user_id: int, artist_id: int) -> None: ...
    async def exists(self, user_id: int, artist_id: int) -> bool: ...
    async def get_user_subscriptions(
        self, user_id: int
    ) -> List[ArtistSubscription]: ...
    async def get_user_subscribed_artists(self, user_id: int) -> List[int]: ...


# 🔹 Implementación con SQLAlchemy
class SQLAlchemySubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, artist_id: int) -> ArtistSubscription:
        subscription = ArtistSubscription(
            user_id=user_id, artist_id=artist_id, created_at=date.today()
        )
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def remove(self, user_id: int, artist_id: int) -> None:
        await self.session.execute(
            delete(ArtistSubscription).where(
                ArtistSubscription.user_id == user_id,
                ArtistSubscription.artist_id == artist_id,
            )
        )
        await self.session.commit()

    async def exists(self, user_id: int, artist_id: int) -> bool:
        result = await self.session.execute(
            select(ArtistSubscription).where(
                ArtistSubscription.user_id == user_id,
                ArtistSubscription.artist_id == artist_id,
            )
        )
        return result.scalar_one_or_none() is not None

    # 🔹 NUEVOS MÉTODOS
    async def get_user_subscriptions(self, user_id: int) -> List[ArtistSubscription]:
        """Obtiene todas las suscripciones de un usuario (solo user_id/artist_id;
        el nombre del artista se resuelve vía HTTP en el service, no con un
        join local — artists ya no es una tabla de este servicio)."""
        result = await self.session.execute(
            select(ArtistSubscription)
            .where(ArtistSubscription.user_id == user_id)
            .order_by(ArtistSubscription.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_user_subscribed_artists(self, user_id: int) -> List[int]:
        """Obtiene solo los IDs de los artistas a los que está suscrito un usuario"""
        result = await self.session.execute(
            select(ArtistSubscription.artist_id)
            .where(ArtistSubscription.user_id == user_id)
            .order_by(ArtistSubscription.created_at.desc())
        )
        return list(result.scalars().all())
