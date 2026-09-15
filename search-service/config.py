from pydantic_settings import (
    BaseSettings,
)  # o from pydantic import BaseSettings si usas v1
from pydantic import Field


class Settings(BaseSettings):
    db_url: str = Field(alias="db_url_py")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(alias="JWT_ALGORITHM", default="HS256")
    port: int = Field(alias="SEARCH_PORT", default=8006)

    fronted_origins_raw: str = Field(alias="FRONTEND_ORIGINS", default="http://localhost:5173")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def frontend_origins(self) -> list[str]:
        """Devuelve la lista de orígenes para CORS."""
        raw = self.fronted_origins_raw
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


settings = Settings()  # type: ignore

# Logs de configuración
print(f"🔧 Config loaded:")
print(f"   JWT Secret: {settings.jwt_secret}")
print(f"   JWT Algorithm: {settings.jwt_algorithm}")
print(f"   Port: {settings.port}")
print(f"   Frontend Origins: {settings.frontend_origins}")