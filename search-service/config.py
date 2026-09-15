from pydantic import Field

from vibestream_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    port: int = Field(alias="SEARCH_PORT", default=8006)


settings = Settings()  # type: ignore
