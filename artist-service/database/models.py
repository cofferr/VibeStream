"""artist-service es dueño exclusivo de la tabla artists (Fase 3). users
vive en auth-service y albums/songs/song_artists en content-service — ya no
se declaran aquí como modelos duplicados. user_id deja de ser FK local:
la validación de que el usuario existe la hace auth-service en el
registro/login, no una constraint de BD cross-servicio."""

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, text

from database.connection import Base


class Artist(Base):
    __tablename__ = "artists"
    __table_args__ = {"schema": "music_streaming"}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False)
    artist_name = Column(Text, unique=True, nullable=False)
    bio = Column(Text, nullable=True)
    profile_pic = Column(String, nullable=True)
    social_links = Column(JSON, nullable=True)

    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
