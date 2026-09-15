"""Configuración base compartida por los servicios Python de VibeStream.

Cada servicio define su propia subclase de BaseServiceSettings agregando
los campos específicos (puerto, RabbitMQ, AWS, etc.), heredando db_url,
jwt_secret/jwt_algorithm y el parseo de CORS.
"""

import json
import logging
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class BaseServiceSettings(BaseSettings):
    db_url: str = Field(alias="db_url_py")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(alias="JWT_ALGORITHM", default="HS256")

    frontend_origins_raw: str = Field(
        alias="FRONTEND_ORIGINS", default="http://localhost:5173"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def frontend_origins(self) -> List[str]:
        """Devuelve la lista de orígenes permitidos para CORS."""
        raw = self.frontend_origins_raw
        if not raw or raw.strip() == "":
            return ["*"]
        s = raw.strip()
        if s == "*":
            return ["*"]
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if x]
            except Exception:
                logger.warning(
                    "FRONTEND_ORIGINS parece una lista JSON pero no pudo parsearse; "
                    "se usará el parseo por comas como fallback: %r",
                    raw,
                )
        return [p.strip() for p in s.split(",") if p.strip()]


class InternalServiceURLsMixin(BaseSettings):
    """Mixin opcional para servicios que necesitan llamar a otros servicios
    internos vía HTTP (Fase 3: propiedad de datos por servicio). Usa los
    nombres DNS de Docker Compose (misma red vibestream-network)."""

    content_service_url: str = Field(
        alias="CONTENT_SERVICE_URL", default="http://content-service:8001"
    )
    artist_service_url: str = Field(
        alias="ARTIST_SERVICE_URL", default="http://artist-service:8002"
    )
    auth_service_url: str = Field(
        alias="AUTH_SERVICE_URL", default="http://auth-service:8080"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
