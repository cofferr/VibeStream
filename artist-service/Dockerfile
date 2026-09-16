# ======================================
# Etapa 1: Build — instala dependencias del sistema y de Python en un
# entorno virtual aislado (Fase 6: se copia completo a la imagen final
# sin arrastrar build-essential ni el resto del toolchain de compilación)
# ======================================
FROM python:3.12.3-slim AS builder

# Evitar buffers de Python para logs en tiempo real
ENV PYTHONUNBUFFERED=1
# Optimización: no generar bytecode compilado en disco
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Instalar el paquete compartido vibestream_common antes que las
# dependencias propias del servicio para aprovechar el cache de Docker
# (el build context es la raíz del repo, ver docker-compose.yml)
COPY shared-python /shared-python
RUN pip install --no-cache-dir /shared-python

# Copiar solo requirements para aprovechar cache de Docker
COPY artist-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ======================================
# Etapa 2: Runtime — imagen final sin toolchain de compilación, usuario
# no privilegiado
# ======================================
FROM python:3.12.3-slim AS runtime

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"

# curl solo para el HEALTHCHECK — no arrastra un compilador
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password --gecos "" appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser artist-service/ .

USER appuser

ARG SERVICE_PORT
EXPOSE ${SERVICE_PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${ARTIST_PORT}/health || exit 1

# Comando para ejecutar el servidor FastAPI con Uvicorn
# Usa sh -c para expandir la variable de entorno PORT en runtime
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${ARTIST_PORT}"]
