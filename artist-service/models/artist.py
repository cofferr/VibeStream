from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict
from datetime import datetime

# -------------------------------
# DTOs de Entrada (Request)
# -------------------------------


class ArtistCreateSchema(BaseModel):
    """Estructura para registrar un artista"""

    artist_name: str  # ✅ Nuevo campo obligatorio
    bio: Optional[str] = None
    profile_pic: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None


class ArtistUpdateSchema(BaseModel):
    """Estructura para actualizar parcialmente un artista"""

    artist_name: Optional[str] = None  # ✅ Ahora se puede actualizar el nombre
    bio: Optional[str] = None
    profile_pic: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None


# -------------------------------
# DTO de Salida (Response)
# -------------------------------


class ArtistResponseSchema(BaseModel):
    id: int
    user_id: int
    artist_name: str  # ✅ Lo incluimos en la respuesta
    bio: Optional[str] = None
    profile_pic: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
