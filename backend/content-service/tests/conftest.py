"""Settings (pydantic-settings) se valida en el import de config.py, así
que hace falta setear las env vars requeridas antes de que pytest importe
cualquier módulo de la app. Se volvió necesario en Fase 6: utils/ownership
ahora importa core.services.artist_lookup, que importa config (antes solo
hacía queries locales con el `db` inyectado, sin tocar settings)."""

import os

os.environ.setdefault(
    "db_url_py", "postgresql+asyncpg://test:test@localhost:5432/test"
)
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("AWS_S3_BUCKET", "test-bucket")
