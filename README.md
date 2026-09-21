# VibeStream - Backend

Backend de una plataforma de streaming musical, organizado como microservicios (8 servicios propios + los paquetes compartidos que los sostienen). Este documento cubre solo el backend: no describe el frontend (`front_music_stm/`), que se levanta junto con el resto vía Docker Compose pero no es el foco de este proyecto.

El objetivo de este repositorio es servir de portfolio/referencia técnica: cada decisión de arquitectura (propiedad de datos por servicio, topología de eventos, manejo de errores, testing, endurecimiento de contenedores) está documentada y justificada en `PLAN.md`, incluyendo el razonamiento de por qué se hizo así y qué se descartó explícitamente.

## Arquitectura

Ocho servicios, cada uno dueño exclusivo de sus propias tablas; el resto los consume vía HTTP interno o eventos de RabbitMQ, nunca leyendo la base de datos de otro servicio directamente.

| Servicio | Lenguaje | Puerto | Responsabilidad | Tablas propias |
|---|---|---|---|---|
| auth-service | Go (Gin) | 8080 | Autenticación, usuarios, JWT | `users`, `jwt.refresh_tokens` |
| artist-service | Python (FastAPI) | 8002 | Perfiles de artista | `artists` |
| content-service | Python (FastAPI) | 8001 | Álbumes, canciones, géneros | `albums`, `songs`, `genres`, `song_artists` |
| playlist-service | Python (FastAPI) | 8004 | Playlists | `playlists`, `playlist_songs` |
| history-service | Go (Gin) | 8005 | Historial de reproducción | `play_history` |
| search-service | Python (FastAPI) | 8006 | Búsqueda difusa (rapidfuzz) | `search_index` (índice CQRS, alimentado por eventos) |
| subscription-service | Python (FastAPI) | 8007 | Suscripciones a artistas | `artist_subscriptions` |
| streaming-service | Go (Gin) | 8003 | Streaming de audio con soporte de rangos HTTP | (sin tablas propias, sirve archivos de content-service) |

Servicios de infraestructura, todos en `docker-compose.yml`:

| Servicio | Puerto | Propósito |
|---|---|---|
| postgres | 5432 | Base de datos única (un schema por dominio, un dueño por tabla) |
| rabbitmq | 5672 / 15672 (management) | Eventos entre servicios (exchanges fanout + dead-letter queue) |
| localstack | 4566 | Emula S3 para desarrollo local, sin credenciales AWS reales |

## Stack técnico

- Go (Gin) para auth-service, history-service y streaming-service, con un módulo compartido (`shared-go/`) para JWT, CORS, DLQ y helpers de respuesta HTTP.
- Python (FastAPI) para los 5 servicios restantes, con un paquete compartido instalable (`shared-python/vibestream_common`) para el mismo tipo de código repetido: middleware de auth, conexión a BD, manejo de errores, cliente HTTP interno, topología de RabbitMQ.
- PostgreSQL como base de datos, con Alembic gestionando las migraciones de content-service y artist-service, y SQL versionado a mano para auth-service (documentado el porqué de esa elección en el propio archivo de migración).
- RabbitMQ con exchanges fanout consistentes y una dead-letter queue compartida — un mensaje que un consumer no puede procesar no se pierde ni reintenta infinito.
- LocalStack para emular S3 en desarrollo local (content-service, artist-service y streaming-service detectan `AWS_ENDPOINT_URL` y usan el emulador en vez de AWS real).
- JWT (HS256) para autenticación y autorización entre clientes y servicios.

## Prerrequisitos

- Docker y Docker Compose
- Git
- 4GB de RAM mínimo
- 2GB de espacio libre en disco

## Instalación y arranque

El stack es autocontenido: `docker compose up` levanta Postgres, RabbitMQ y LocalStack junto con los 8 servicios, sin necesitar una base de datos externa ni credenciales AWS reales. Postgres se bootstrapea solo con el schema completo (`schema_reconstruido.sql`) la primera vez que arranca con un volumen vacío.

1. Clonar el repositorio

```bash
git clone https://github.com/cofferr/VibeStream.git
cd VibeStream
```

2. Configurar variables de entorno

```bash
cp .env.example .env
```

Los valores por defecto de `.env.example` ya funcionan para desarrollo local (Postgres y LocalStack incluidos en el compose). Editar solo si se necesita apuntar a servicios reales (una base de datos externa, AWS real, credenciales de RabbitMQ propias).

3. Levantar los servicios

```bash
docker compose build
docker compose up
```

Para levantar solo un subconjunto:

```bash
docker compose up -d auth-service content-service postgres rabbitmq
```

4. Verificar que los servicios estén corriendo

```bash
docker compose ps
```

Los 11 servicios (8 backend + postgres + rabbitmq + localstack, más el frontend) deberían quedar en estado `healthy` — cada uno tiene un `HEALTHCHECK` real, no solo "está corriendo".

5. Acceder a la infraestructura

- RabbitMQ Management: http://localhost:15672 (usuario/contraseña definidos en `.env`, `guest`/`guest` por defecto)
- LocalStack (S3 emulado): http://localhost:4566
- Cada servicio expone `GET /health` en su propio puerto (ver tabla de arriba)

## Variables de entorno

Ver `.env.example` para la lista completa y comentada. Los grupos principales:

- `db_url_py` / `DB_URL`: conexión a Postgres (formato distinto para asyncpg vs. el driver de Go).
- `JWT_SECRET` / `JWT_ALGORITHM`: deben coincidir en los 8 servicios (todos validan el mismo token).
- `RABBITMQ_USER` / `RABBITMQ_PASS` / `RABBITMQ_URL`: credenciales del broker — si se cambian las dos primeras, `RABBITMQ_URL` debe actualizarse a mano (docker-compose no soporta variables derivadas de otras variables dentro del mismo `.env`).
- `*_SERVICE_URL`: URLs internas usadas por los servicios que se llaman entre sí vía HTTP (nombres DNS de Docker Compose).
- `AWS_ENDPOINT_URL` / `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` / `AWS_S3_BUCKET`: configuración de almacenamiento de archivos. Con `AWS_ENDPOINT_URL` seteado (como viene por defecto) se usa LocalStack; sin esa variable, el mismo código se conecta a AWS real.

## Comandos útiles

```bash
# Ver estado y healthchecks de los contenedores
docker compose ps

# Ver logs de un servicio específico
docker compose logs -f content-service

# Reiniciar un servicio
docker compose restart streaming-service

# Reconstruir y levantar
docker compose up -d --build

# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes (borra los datos de Postgres/LocalStack)
docker compose down -v

# Acceder a un contenedor
docker exec -it content-service sh

# Ver uso de recursos
docker stats
```

## Testing y CI

- Go: `go test ./...` en auth-service, history-service y streaming-service (usa la stdlib `testing` + `net/http/httptest`, sin framework externo). Lint con `golangci-lint` (`govet`, `staticcheck`, `errcheck`).
- Python: `pytest` en los 5 servicios, con `pytest-asyncio` y fixtures de SQLite en memoria para los tests de repositorio (no requieren Postgres real). Lint con `ruff`.
- `.github/workflows/ci.yml` corre ambos conjuntos de tests y linters en matrix por servicio en cada push/PR.

No es cobertura exhaustiva a propósito: 1-2 tests de alto valor por servicio, enfocados en la lógica que de verdad puede romperse (errores tipados, validaciones de ownership, manejo de fallos de infraestructura), no en volumen de casos.

## Estructura del proyecto

```
VibeStream/
├── auth-service/          # Autenticación, usuarios, JWT (Go)
├── artist-service/        # Perfiles de artista (Python)
├── content-service/       # Álbumes, canciones, géneros (Python)
├── playlist-service/      # Playlists (Python)
├── history-service/       # Historial de reproducción (Go)
├── search-service/        # Búsqueda difusa (Python)
├── subscription-service/  # Suscripciones a artistas (Python)
├── streaming-service/     # Streaming de audio (Go)
├── shared-go/             # Código Go compartido (JWT, CORS, DLQ, respuestas HTTP)
├── shared-python/         # Paquete Python compartido (vibestream_common)
├── localstack/            # Script de inicialización del bucket S3 emulado
├── front_music_stm/       # Frontend React (fuera del alcance de este documento)
├── schema_reconstruido.sql  # Snapshot completo del schema, usado para bootstrapear Postgres
├── docker-compose.yml     # Orquestación de los 11 servicios
├── PLAN.md                # Historial completo de decisiones de arquitectura, fase por fase
└── .env.example           # Plantilla de variables de entorno
```

## Documentación de arquitectura

`PLAN.md` contiene el historial completo de este proyecto: los problemas encontrados en la auditoría original, las decisiones tomadas para resolverlos, y la verificación real de cada cambio contra un stack Docker en funcionamiento — no solo la intención, sino qué se probó y qué quedó pendiente. Es el documento de referencia para entender por qué el código está como está.
