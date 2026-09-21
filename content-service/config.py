# config.py
from typing import Optional

import boto3
from botocore.config import Config
from pydantic import Field
from vibestream_common.config import BaseServiceSettings, InternalServiceURLsMixin


class Settings(BaseServiceSettings, InternalServiceURLsMixin):
    port: int = Field(alias="CONTENT_PORT", default=8001)
    rabbitmq_url: str = Field(alias="RABBITMQ_URL")

    # === AWS S3 CONFIG — OBLIGATORIO ===
    aws_access_key_id: str = Field(alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(alias="AWS_SECRET_ACCESS_KEY")
    aws_session_token: Optional[str] = Field(default=None, alias="AWS_SESSION_TOKEN")
    aws_region: str = Field(alias="AWS_REGION")
    aws_s3_bucket: str = Field(alias="AWS_S3_BUCKET")
    # Si está seteado, boto3 apunta a un S3 emulado (LocalStack) en vez de
    # AWS real — permite probar el flujo de upload completo sin
    # credenciales AWS reales. Ver docker-compose.yml (servicio
    # `localstack`) y .env.example.
    aws_endpoint_url: Optional[str] = Field(default=None, alias="AWS_ENDPOINT_URL")

    # === STORAGE SETTINGS ===
    max_file_size: int = Field(default=15 * 1024 * 1024)
    allowed_image_types: list = Field(
        default=["image/jpeg", "image/png", "image/jpg", "image/gif"]
    )

    def get_s3_client(self):
        args = {
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
            "region_name": self.aws_region,
        }
        if self.aws_session_token:
            args["aws_session_token"] = self.aws_session_token
        if self.aws_endpoint_url:
            args["endpoint_url"] = self.aws_endpoint_url
            # LocalStack no resuelve el addressing "virtual hosted"
            # (bucket.s3.amazonaws.com) que boto3 usa por default.
            args["config"] = Config(s3={"addressing_style": "path"})

        return boto3.client("s3", **args)

    def get_public_base_url(self) -> str:
        """
        Devuelve la URL base pública del bucket.
        """
        if self.aws_endpoint_url:
            return f"{self.aws_endpoint_url}/{self.aws_s3_bucket}"
        return f"https://{self.aws_s3_bucket}.s3.{self.aws_region}.amazonaws.com"


settings = Settings()
