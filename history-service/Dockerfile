# ======================================
# Dockerfile genérico para microservicios Go
# ======================================

# ======================================
# Etapa 1: Build
# ======================================
FROM golang:1.24.5 AS builder

# Definir directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias primero para aprovechar cache de Docker
COPY go.mod go.sum ./
RUN go mod download

# Copiar el resto del código fuente
COPY . .

# ARG para el nombre del servicio (se pasa desde docker-compose)
ARG SERVICE_NAME=service

# Compilar el binario para Linux con optimizaciones
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a -installsuffix cgo \
    -o ${SERVICE_NAME} .

# ======================================
# Etapa 2: Runtime
# ======================================
FROM alpine:3.19

# Instalar dependencias mínimas del sistema
RUN apk add --no-cache ca-certificates curl

# Crear usuario no privilegiado para seguridad
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

WORKDIR /app

# ARGs para configuración dinámica
ARG SERVICE_NAME=service
ARG SERVICE_PORT=8080

# Variables de entorno
ENV SERVICE_NAME=${SERVICE_NAME}
ENV PORT=${SERVICE_PORT}

# Copiar binario desde la etapa de build con permisos correctos
COPY --from=builder --chown=appuser:appgroup /app/${SERVICE_NAME} .

# Cambiar a usuario no privilegiado
USER appuser

# Exponer puerto dinámico
EXPOSE ${SERVICE_PORT}

# Comando de inicio dinámico
CMD ./${SERVICE_NAME}
