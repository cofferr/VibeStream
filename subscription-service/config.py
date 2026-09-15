from pydantic_settings import (
    BaseSettings,
)  # o from pydantic import BaseSettings si usas v1
from pydantic import Field


class Settings(BaseSettings):
    db_url: str = Field(alias="db_url_py")
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    port: int = Field(alias="SUBSCRIPTION_PORT", default=8007)
    # Orígenes permitidos para CORS (configurable)
    frontend_origins_raw: str = Field(alias="FRONTEND_ORIGINS", default="http://localhost:5173")

    @property
    def frontend_origins(self) -> list[str]:
        raw = self.frontend_origins_raw
        if not raw or raw.strip() == "":
            return ["*"]
        s = raw.strip()
        if s == "*":
            return ["*"]
        if s.startswith("[") and s.endswith("]"):
            try:
                import json

                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if x]
            except Exception:
                pass
        return [p.strip() for p in s.split(",") if p.strip()]

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore
