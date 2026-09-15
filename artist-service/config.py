from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List, Optional
import boto3
import json


class Settings(BaseSettings):
    # === DATABASE & APP CONFIG ===
    db_url: str = Field(alias="db_url_py")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(alias="JWT_ALGORITHM", default="HS256")
    port: int = Field(alias="ARTIST_PORT", default=8002)
    rabbitmq_url: str = Field(alias="RABBITMQ_URL")

    # === CORS ===
    frontend_origins_raw: str = Field(
        alias="FRONTEND_ORIGINS", default="http://localhost:5173"
    )

    # === AWS S3 CONFIG ===
    aws_access_key_id: str = Field(alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(alias="AWS_SECRET_ACCESS_KEY")
    aws_session_token: Optional[str] = Field(default=None, alias="AWS_SESSION_TOKEN")
    aws_region: str = Field(alias="AWS_REGION")
    aws_s3_bucket: str = Field(alias="AWS_S3_BUCKET")

    # === STORAGE SETTINGS ===
    max_file_size: int = Field(default=15 * 1024 * 1024)
    allowed_image_types: list = Field(
        default=["image/jpeg", "image/png", "image/jpg", "image/gif"]
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def frontend_origins(self) -> List[str]:
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
        return [p.strip() for p in s.split(",") if p.strip()]

    def get_s3_client(self):
        """Devuelve un cliente boto3 configurado para S3."""
        args = {
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
            "region_name": self.aws_region,
        }
        if self.aws_session_token:
            args["aws_session_token"] = self.aws_session_token
        return boto3.client("s3", **args)

    def get_public_base_url(self) -> str:
        """
        Devuelve la URL base pública del bucket.
        Ej: https://mi-bucket.s3.us-east-2.amazonaws.com
        """
        return f"https://{self.aws_s3_bucket}.s3.{self.aws_region}.amazonaws.com"


settings = Settings()  # type: ignore

print(f"🔧 Configuración cargada:")
print(f"   AWS Región: {settings.aws_region}")
print(f"   AWS Bucket: {settings.aws_s3_bucket}")
print(f"   URL Base:   {settings.get_public_base_url()}")
