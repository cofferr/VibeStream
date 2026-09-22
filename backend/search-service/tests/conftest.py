"""Settings (pydantic-settings) se valida en el import de config.py, así
que hace falta setear las env vars requeridas antes de que pytest
importe cualquier módulo de la app — no hace falta un valor real, los
tests de esta carpeta no tocan BD ni RabbitMQ de verdad."""

import os

os.environ.setdefault(
    "db_url_py", "postgresql+asyncpg://test:test@localhost:5432/test"
)
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
