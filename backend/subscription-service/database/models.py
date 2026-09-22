from sqlalchemy import Column, Date, Integer
from vibestream_common.db import Base


class ArtistSubscription(Base):
    """subscription-service es dueño exclusivo de esta tabla (Fase 3).
    user_id y artist_id ya no son FK locales: users vive en auth-service y
    artists en artist-service. La validación de que ambos existen se hace
    vía llamada HTTP (ver services/subscription_service.py), no vía
    constraint de BD — es un límite de consistencia lógico, no físico."""

    __tablename__ = "artist_subscriptions"
    __table_args__ = {"schema": "music_streaming"}

    user_id = Column(Integer, primary_key=True, nullable=False)
    artist_id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column(Date)
