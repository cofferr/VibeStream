from pydantic import Field

from vibestream_common.config import BaseServiceSettings, InternalServiceURLsMixin


class Settings(BaseServiceSettings, InternalServiceURLsMixin):
    port: int = Field(alias="SEARCH_PORT", default=8006)
    rabbitmq_url: str = Field(alias="RABBITMQ_URL")


settings = Settings()  # type: ignore
