from pydantic import Field
from vibestream_common.config import BaseServiceSettings, InternalServiceURLsMixin


class Settings(BaseServiceSettings, InternalServiceURLsMixin):
    port: int = Field(alias="SUBSCRIPTION_PORT", default=8007)


settings = Settings()  # type: ignore
