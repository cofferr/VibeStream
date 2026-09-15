from sqlalchemy import select
from infrastructure.db.models import Artist
from sqlalchemy.ext.asyncio import AsyncSession


class ArtistLookupService:
    @staticmethod
    async def get_artist_id_by_user(user_id: int, db: AsyncSession):
        """
        Obtiene el artist_id basado en el user_id
        Retorna None si no se encuentra el artista
        """
        try:
            stmt = select(Artist.id).where(Artist.user_id == user_id)
            result = await db.scalar(stmt)
            return result
        except Exception as e:
            print(f"Error en get_artist_id_by_user: {e}")
            return None
