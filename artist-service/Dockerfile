
# ======================================
# Etapa 1: Base para dependencias
# ======================================
FROM python:3.12.3-slim AS base

# Evitar buffers de Python para logs en tiempo real
ENV PYTHONUNBUFFERED=1
# Optimización: no generar bytecode compilado en disco
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias de sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Definir directorio de trabajo
WORKDIR /app

# Copiar solo requirements para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# ======================================
# Etapa 2: Copiar código y ejecutar
# ======================================
FROM base AS runtime

WORKDIR /app

# Copiar todo el código del microservicio
COPY . .

# Exponer el puerto dinámico desde variable de entorno
ARG SERVICE_PORT
EXPOSE ${SERVICE_PORT}

# Comando para ejecutar el servidor FastAPI con Uvicorn
# Usa sh -c para expandir la variable de entorno PORT en runtime
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${ARTIST_PORT}"]
