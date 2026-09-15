# config.py
from pydantic import Field

from vibestream_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    port: int = Field(alias="PLAYLIST_PORT", default=8004)
    # URL base para acceder a archivos (covers/audio) desde otros servicios
    files_base_url: str = Field(
        alias="FILES_BASE_URL", default="http://localhost:8002/files"
    )


settings = Settings()
