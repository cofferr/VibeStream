# config.py
from pydantic import Field
from vibestream_common.config import BaseServiceSettings, InternalServiceURLsMixin


class Settings(BaseServiceSettings, InternalServiceURLsMixin):
    port: int = Field(alias="PLAYLIST_PORT", default=8004)


settings = Settings()
