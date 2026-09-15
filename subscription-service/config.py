from pydantic import Field

from vibestream_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    port: int = Field(alias="SUBSCRIPTION_PORT", default=8007)


settings = Settings()  # type: ignore
