# config.py - VERIFICAR QUE LAS URLS ESTÉN CORRECTAS
from pydantic_settings import BaseSettings
from pydantic import Field
import json
from typing import List

class Settings(BaseSettings):
    db_url: str = Field(alias="db_url_py")
    jwt_secret: str = Field(alias="JWT_SECRET", default="HolaMundoo")
    jwt_algorithm: str = Field(alias="JWT_ALGORITHM", default="HS256")
    port: int = Field(alias="PLAYLIST_PORT", default=8004)
    frontend_origins_raw: str = Field(alias="FRONTEND_ORIGINS", default="http://localhost:3000,http://localhost:5173")
    # URL base para acceder a archivos (covers/audio) desde otros servicios
    files_base_url: str = Field(alias="FILES_BASE_URL", default="http://localhost:8002/files")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def frontend_origins(self) -> List[str]:
        """Devuelve la lista de orígenes para CORS."""
        raw = self.frontend_origins_raw
        if not raw or raw.strip() == "":
            return ["*"]  # Permitir todos si no está configurado
        s = raw.strip()
        if s == "*":
            return ["*"]  # Wildcard explícito
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if x]
            except Exception:
                pass
        # Normalizar a lista separada por comas
        return [p.strip() for p in s.split(",") if p.strip()]

settings = Settings()

print(f"🔧 Config loaded:"
      f"\n   JWT Secret: {settings.jwt_secret}"
      f"\n   JWT Algorithm: {settings.jwt_algorithm}"
      f"\n   Port: {settings.port}"
    f"\n   Frontend Origins: {settings.frontend_origins}"
    f"\n   Files Base URL: {settings.files_base_url}"
)