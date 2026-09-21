# Plan de remediación de código y arquitectura — VibeStream

## Contexto

El análisis previo del repo (revisión de código Go/Python, flujo de RabbitMQ, Docker/AWS) encontró problemas concretos que comprometerían la defensa de este proyecto en una entrevista técnica: secretos hardcodeados y logueados en texto plano, una arquitectura de "microservicios" que en realidad comparte una sola base de datos sin fronteras reales (varios servicios duplican tablas ajenas), manejo de errores inconsistente que filtra detalles internos al cliente, RabbitMQ parcialmente cableado sin DLQ, y cero tests/CI/linting en todo el repo.

El objetivo de este plan es exclusivamente de **portfolio/entrevista**: cada decisión que quede en el código debe poder explicarse y defenderse ("encontré X, era un problema porque Y, lo resolví con Z"). No es un plan de *production hardening* para tráfico real — por eso el testing es deliberadamente mínimo pero real, y el compose sigue siendo apto para demo local, no para producción con límites de recursos estrictos.

Se confirmaron tres decisiones de arquitectura antes de este plan:
- **`artist-service` es el dueño real de la tabla `artists`** (es quien la escribe hoy); `content-service` deja de declarar su propio modelo `Artist` y la consulta vía HTTP.
- **`search-service` mantiene un índice local propio (`search_index`)** alimentado por eventos de RabbitMQ de `content-service`, en vez de golpear su API en cada búsqueda — es el patrón CQRS correcto para búsqueda difusa (usa `rapidfuzz`).
- **El testing es mínimo pero real**: 1-2 tests de alto valor por servicio más CI que efectivamente falla si algo se rompe, no cobertura exhaustiva.

Cada fase deja el repo en estado funcional (`docker compose up` sigue funcionando) — ninguna fase depende de una fase futura para ser segura de detenerse ahí.

---

## Fase 0 — Seguridad crítica (rápida, sin riesgo arquitectónico)

**Objetivo:** eliminar lo que un entrevistador notaría en los primeros 30 segundos.

**Archivos:**
- `auth-service/config/config.go:25` — quitar el fallback hardcodeado `"HolaMundoo"`; fallar rápido (`log.Fatal`) si `JWT_SECRET` no está seteado.
- `history-service/config/config.go`, `streaming-service/config/config.go` — mismo fix, quitar `"defaultsecret"`.
- `search-service/config.py:44-45` — eliminar el `print(f"JWT Secret: {settings.jwt_secret}")` (imprime el secreto completo en cada arranque del contenedor).
- `artist-service/middleware/auth_middleware.py`, `content-service/middleware/auth_middleware.py` — quitar los prints de debug que exponen parte del secreto JWT.
- `auth-service/middleware/auth.go` — reemplazar `github.com/dgrijalva/jwt-go` (archivada, con CVEs) por `github.com/golang-jwt/jwt/v5` (ya usada correctamente en `auth-service/services/auth_service.go`), unificando a una sola librería JWT en el servicio. Actualizar `go.mod`/`go.sum` con `go mod tidy`.
- `.env.example` — confirmar que solo tiene placeholders (ya se ve correcto).

**Verificación:**
- `grep -rn "HolaMundoo\|defaultsecret" auth-service history-service streaming-service` → sin resultados.
- `grep -rn "print.*jwt_secret" search-service` → sin resultados.
- `grep -rn "dgrijalva" auth-service` → sin resultados; `go build ./...` compila en auth-service.
- `docker compose up auth-service` sin `JWT_SECRET` en `.env` falla rápido con mensaje claro (prueba intencional del fail-fast).

---

## Fase 1 — Estandarizar manejo de errores (por lenguaje, sin acoplar servicios todavía)

**Objetivo:** cada servicio devuelve errores saneados al cliente y loguea el detalle completo server-side, con un patrón reusable por lenguaje. Todavía cada servicio es independiente (la Fase 2 convierte esto en librería compartida).

**Go:**
- Nuevo helper `RespondError(c *gin.Context, status int, logErr error, publicMsg string)` en cada servicio (ej. `auth-service/utils/errors.go`) que loguea `logErr` server-side y devuelve solo `publicMsg` al cliente.
- `auth-service/handlers/login.go:32`, `register.go:33`, `update.go:50`, `get_user.go:40`, `refresh.go:27` — reemplazar `c.JSON(status, gin.H{"error": err.Error()})` por el helper saneado.
- `auth-service/handlers/login.go:25-30`, `update.go:43-48` — reemplazar el switch sobre string de error por errores centinela tipados (`var ErrUserNotFound = errors.New(...)` en `auth-service/services/auth_service.go` + `errors.Is`).
- `streaming-service/handlers/stream.go:67,77,100,131` — dejar de exponer texto crudo de errores S3/AWS; loguear y devolver mensaje genérico.
- `streaming-service/handlers/stream.go:107,150,163` — reemplazar `fmt.Printf` por logger consistente.
- `history-service/handlers/history_handler.go:44` y `history-service/events/consumer.go:67,73` quedan como referencia del buen patrón — sin cambios.

**Python:**
- Nuevo `core/errors.py` (o `utils/errors.py`) por servicio con excepciones propias (`NotFoundError`, `ValidationError`) y un `@app.exception_handler(Exception)` global que loguea con `logging` (no `print`) y devuelve JSON saneado — replicando el patrón ya bueno de `artist-service/main.py:41-49`.
- `content-service/main.py` — agregar el handler global (falta hoy); `content-service/core/handlers/album_handler.py:54,71` dejar de devolver `str(e)`; reemplazar `print()` por `logging` ahí y en `content-service/config.py:59`.
- `content-service/core/handlers/song_handler.py:23-30` — mover de `Form(...)` a body Pydantic validado donde sea posible (manteniendo `UploadFile` para el archivo de audio).
- `playlist-service/handlers/playlist_handlers.py` (7+ sitios: líneas 105-107, 141-143, 189-191, 225-227, 264-266, 305-307, 404-406) — el peor caso del repo; implementar un decorador `@handle_errors` en este servicio primero (se promueve a librería compartida en Fase 2).
- `playlist-service/repositories/playlist_repository.py:183,211,242,255` — dejar de devolver silenciosamente `False`/`[]`/`0` en `except Exception:` bare; re-lanzar como `RepositoryError` tipado para distinguir "vacío legítimo" de "falló".
- `search-service/handlers/search_handler.py:39-43` — quitar `str(e)` y el print de traceback completo.
- `search-service/strategies/fuzzy_strategy.py:29,76`, `search-service/services/search_service.py:31,41,51,73` — dejar de silenciar excepciones sin loguear; acotar a los tipos de excepción esperados.
- `artist-service/handlers/artist_handler.py:55,116` — no descartar el mensaje de excepción antes de re-lanzar; usar `raise ... from e` o loguear antes.
- `artist-service/config.py:51`, `subscription-service/config.py:30` — reemplazar `except: pass` por manejo acotado y logueado.

**Verificación:**
- `grep -rn "str(e)"` en playlist-service/content-service/search-service → solo dentro de `logging.exception(...)`, nunca en la respuesta JSON.
- Disparar manualmente un 500 en cada servicio y confirmar que el body es genérico mientras `docker compose logs <servicio>` muestra el stack trace real.

---

## Fase 2 — Extraer código duplicado a paquetes compartidos

**Objetivo:** convertir el middleware JWT, la conexión a BD, CORS/config y el patrón de errores de la Fase 1 (todos ~90% idénticos entre servicios del mismo lenguaje) en código realmente compartido, con un mecanismo concreto dado que son servicios Docker desplegados independientemente.

**Python — nuevo paquete `shared-python/` (`vibestream_common`):**
- `vibestream_common/auth_middleware.py` (consolidado de los 5 `middleware/auth_middleware.py` casi idénticos)
- `vibestream_common/db.py` (el boilerplate `create_async_engine` + `async_sessionmaker` + `get_db()`)
- `vibestream_common/config.py` (clase base `Settings(BaseSettings)` con la propiedad `frontend_origins`, corrigiendo de paso el typo `fronted_origins_raw` de search-service)
- `vibestream_common/errors.py` (el patrón de la Fase 1)
- Mecanismo de build: cambiar el `context:` de build de los 5 servicios Python en `docker-compose.yml` de `./<servicio>` a `.` (raíz del repo) con `dockerfile: <servicio>/Dockerfile`; cada Dockerfile hace `COPY shared-python /shared-python && pip install /shared-python` antes de copiar el código del servicio. Nota para la entrevista: en producción real esto sería un paquete versionado en un índice privado; aquí un install por path es la elección pragmática dado el tamaño del repo.
- Borrar los 5 `middleware/auth_middleware.py`, los 5 `database/connection.py`, y la sección CORS/`frontend_origins` de cada `config.py`, reemplazando por imports de `vibestream_common`.

**Go — `go.work` + módulo interno `shared-go/`:**
- `shared-go/httpresponse/` (el helper `RespondError` de la Fase 1)
- `shared-go/authclaims/` (lógica JWT compartida de los 3 `middleware/auth.go`, resolviendo a un solo comportamiento correcto las divergencias actuales en manejo de OPTIONS y coerción de tipo de `user_id`)
- `go.work` en la raíz listando `./auth-service`, `./history-service`, `./streaming-service`, `./shared-go`; cada `go.mod` de servicio usa `replace vibestream/shared => ../shared-go`. Para Docker: mismo truco que en Python — ampliar el build context a la raíz y `COPY shared-go` antes de `go build`.
- `history-service/main.go:42-56` — reemplazar el CORS hecho a mano por `gin-contrib/cors` (igual que auth-service y streaming-service), eliminando la única divergencia real de CORS en Go.

**Verificación:**
- `docker compose build --no-cache` compila los 8 servicios desde cero (prueba que los build contexts ampliados funcionan).
- `go build ./...` desde la raíz usando `go.work`.
- Diff de líneas: las ~470 líneas de middleware JWT Go y ~176 líneas de boilerplate de conexión Python colapsan a una sola implementación compartida — buen dato para la entrevista.

---

## Fase 3 — Refactor de propiedad de datos (un dueño por tabla)

**Objetivo:** `content-service`, `artist-service` y `auth-service` quedan como únicos dueños/escritores de sus tablas. El resto deja de declarar modelos duplicados y consume vía HTTP interno.

**Propiedad final:** `auth-service` → `users`; `artist-service` → `artists`; `content-service` → `albums`, `songs`, `genres`, `song_artists`; `subscription-service` → `artist_subscriptions` (propia); `playlist-service` → `playlists`, `playlist_songs` (propia); `search-service` → `search_index` (propia, ver Fase 4).

**Paso 1 — exponer lo que otros necesitan:**
- `content-service/core/handlers/` — agregar endpoints de lectura: song por id (con datos ya enriquecidos de álbum/artista para evitar N llamadas), álbum por id, y un endpoint batch "songs por lista de ids" (playlist-service y search-service lo necesitan).
- `artist-service/handlers/artist_handler.py` — agregar "artista por id" (público, sin auth) para que content-service, search-service y subscription-service puedan resolver/validar datos de artista.
- `auth-service/handlers/` — agregar "usuario por id" con campos públicos únicamente, para playlist-service/subscription-service que hoy leen `users` directo.

**Paso 2 — cliente HTTP interno:**
- Python: `vibestream_common/http_client.py` (parte del paquete de la Fase 2) envolviendo `httpx.AsyncClient`, con URLs base leídas de settings (`CONTENT_SERVICE_URL`, `ARTIST_SERVICE_URL`, `AUTH_SERVICE_URL`) usando los nombres DNS de Docker Compose ya disponibles en `vibestream-network` (ej. `http://content-service:8001`). Agregar estas variables a `.env.example` y `docker-compose.yml`.

**Paso 3 — borrar modelos duplicados y recablear:**
- `artist-service/database/models.py` — mantener `Artist`, borrar `User`/`Album`/`Song`/`SongArtist` duplicados.
- `search-service/database/models.py` y `search-service/entities/schema.py` — borrar por completo. `search-service/repositories/*.py` deja de hacer `select(Song)`/`select(Album)`/`select(Artist)` directo; pasa a construirse desde el índice local de la Fase 4 (no desde llamadas HTTP síncronas, que serían demasiado lentas para `rapidfuzz`).
- `subscription-service/database/models.py` — borrar `User` y `Artist` duplicados, mantener solo `ArtistSubscription`. Validar `artist_id` llamando al nuevo endpoint de artist-service antes de insertar la suscripción.
- `playlist-service/database/models.py` — borrar `User`, `Artist`, `Album`, `Song` duplicados. El cambio más grande: `playlist-service/repositories/playlist_repository.py` (líneas ~89-115) hace hoy un join SQL real Song→Album→Artist para construir la vista enriquecida de la playlist. Pasa a: playlist-service guarda solo `song_id` (sin FK cross-schema) en su propia tabla, y `playlist-service/services/playlist_service.py` llama al endpoint batch de content-service para enriquecer la lista de ids después de traer los ids propios de su BD. Es el trade-off estándar y correcto de microservicios — buen punto de entrevista sobre límites de consistencia.
- `schema_reconstruido.sql` — anotar con comentarios qué servicio es dueño de cada `CREATE TABLE`, documentando las FKs cross-schema que ahora son "lógicas" (aplicadas vía el cliente HTTP, no como constraint de BD).

**Verificación:**
- `grep -rln "class User\|class Artist\|class Album\|class Song" */database/models.py */entities/*.py` → solo debe aparecer `content-service` (Album/Song/Genre), `artist-service` (Artist), y `auth-service/models/user.go` (Go).
- Crear una playlist, agregar una canción, consultarla — confirmar que los campos enriquecidos (título, artista, portada) siguen apareciendo, ahora vía HTTP en vez de join local.
- `docker compose up` arranca correctamente con las nuevas variables `*_SERVICE_URL`.

### ✅ Estado: implementada y verificada con Docker (2026-09-15)

Implementada originalmente en una máquina sin Docker disponible (validada solo con `go build` + chequeo de sintaxis Python + trazado manual). En esta sesión se corrió la verificación real pendiente: `docker compose build --no-cache` (9 servicios, incluyendo el build context ampliado a raíz de Fase 2) y `docker compose up`, con un Postgres temporal (fuera de `docker-compose.yml`, ver nota) cargado con `schema_reconstruido.sql`.

**Flujo de punta a punta probado y funcionando:** registro de usuario/login (auth-service) → registro de artista → álbum "Sencillos" automático vía evento `artist_created` → canción indexada → playlist creada con la canción, enriquecida vía HTTP a content-service (título/artista/álbum/portada) → búsqueda difusa por texto encuentra canción/álbum/artista vía `search_index` → editar perfil de artista dispara `artist_updated` (fanout) y reindexa en `search_index` → eliminar artista dispara cascada real vía `DELETE /albums/artist/{id}` (álbumes y canciones borrados en `content-service`, confirmado en BD).

**Nota:** `docker-compose.yml` no incluye un servicio Postgres (el proyecto original asume una BD externa, p. ej. RDS, fuera del repo) — para verificar localmente se levantó un contenedor Postgres temporal por fuera de compose, conectado a la red `vibestream_vibestream-network`. Esto no es parte del repo ni se commiteó; si se quiere que `docker compose up` sea autocontenido para demo/entrevista, agregar un servicio `postgres` a `docker-compose.yml` es trabajo nuevo, no cubierto por ningún fase de este plan — decisión pendiente para el usuario.

**Bugs reales encontrados y corregidos durante esta verificación** (no eran hipótesis — bloqueaban el flujo end-to-end):

1. **`content-service/core/entities/album.py` y `song.py`** — `AlbumOut`, `SongOut` y `SongEnrichedOut` tipaban `created_at`/`updated_at` como `date` cuando la columna real en Postgres es `timestamp`. Pydantic rechazaba la validación con `date_from_datetime_inexact` apenas un álbum/canción tenía un timestamp con hora ≠ medianoche — es decir, siempre. Esto rompía `GET /albums/{id}` y `GET /songs/{id}/enriched`, los dos endpoints exactos que search-service y playlist-service usan para el enriquecimiento HTTP de Fase 3. Corregido a `datetime`.

2. **`shared-python/vibestream_common/auth_middleware.py`** — el middleware lanzaba `HTTPException` dentro de `dispatch()` (un método de `BaseHTTPMiddleware`). Starlette registra el handler pasado a `add_exception_handler(Exception, ...)` como el `error_handler` de `ServerErrorMiddleware`, que envuelve TODOS los middlewares de usuario, no solo las rutas — así que cualquier `HTTPException` lanzada en `AuthMiddleware` era interceptada por ese catch-all antes de llegar al manejo específico de `HTTPException` de FastAPI, y se aplanaba a un 500 genérico. **Resultado: cualquier request sin JWT o con JWT inválido devolvía 500 en vez de 401 en los 5 servicios Python** (bug universal introducido al extraer el middleware a `vibestream_common` en Fase 2, no visible mientras cada servicio tenía su copia porque nunca se probó el flujo real contra un stack completo). Corregido devolviendo `JSONResponse` directamente en vez de `raise`, con headers CORS explícitos (se agregó `cors_origin` al constructor, igual que ya existía para `make_global_exception_handler`).

3. **`playlist-service/main.py` y `subscription-service/main.py`** — nunca registraron el `app.add_exception_handler(Exception, make_global_exception_handler(...))` que sí tienen artist/content/search-service (gap real de Fase 1, no capturado en su momento). Sin él, cualquier excepción no capturada por `@handle_errors`/try-except local salía como texto plano sin headers CORS, lo que el navegador del frontend bloquearía como error de CORS antes de que el JS viera el status real. Agregado en ambos, mismo patrón que los otros 3 servicios.

4. **`artist-service/database/models.py`** — el modelo SQLAlchemy declaraba `created_at`/`updated_at` como `Date` con `server_default/onupdate=CURRENT_DATE`, pero la columna real en Postgres es `timestamp`. Cada `UPDATE` truncaba `updated_at` a medianoche (`2026-09-15T00:00:00`), perdiendo la hora real — mismo patrón de bug que el punto 1 pero del lado de escritura. Corregido a `DateTime`/`CURRENT_TIMESTAMP`.

**Gap real encontrado, no corregido (pendiente de decisión):** al eliminar un artista, sus álbumes/canciones se borran en cascada en `content-service` (confirmado), pero **no se publica ningún evento `artist_deleted`/`song_deleted`/`album_deleted`**, así que las entradas correspondientes quedan huérfanas en `search_index` de search-service — un usuario podría seguir encontrando por búsqueda un artista/álbum/canción ya eliminado. Ninguna fase del plan original cubre eventos de borrado explícitamente. Opciones: (a) agregarlo al alcance de Fase 4 (ya toca la topología de eventos), o (b) documentarlo como limitación aceptada para el alcance de portfolio — buena pregunta de entrevista de todos modos ("¿qué pasa si...?").

**Pendiente real remanente:**
- Subir una canción por el flujo real (`POST /songs`) requiere credenciales AWS S3 válidas — no disponibles en este entorno de verificación. Se probó el resto del flujo insertando una fila de canción directamente en BD y publicando manualmente el evento `song_created` que el endpoint real publicaría; la lógica de enriquecimiento/indexado en sí quedó validada, pero el upload a S3 en sí no se ejercitó end-to-end.
- No se revisó la UI de RabbitMQ manualmente (se usó la API HTTP de management, que confirmó los exchanges fanout `artist_created`/`artist_updated` con sus colas nombradas y las colas bare `song_created`/`song_updated`/`album_created`/`album_updated`, tal como documenta el punto 2 de "Cambios respecto al texto original" arriba).

**Cambios respecto al texto original del plan, decididos con el usuario durante la implementación:**

1. **search-service se adelantó desde Fase 4** en vez de dejarlo con los modelos borrados y la búsqueda rota entre fases. Se implementó ya:
   - `search-service/database/models.py` — nueva tabla `search_index` (CQRS), reemplaza por completo los modelos ORM Song/Album/Artist/User que leían la BD compartida.
   - `search-service/entities/schema.py` — borrado (como pedía el plan).
   - `search-service/events/consumer.py` (nuevo) — consume `song_created`/`song_updated`/`album_created`/`album_updated` de content-service (patrón bare-queue existente, sin fanout) y `artist_created`/`artist_updated` de artist-service (fanout, ver punto 2). Por cada evento, llama al endpoint enriquecido de content-service/artist-service y hace upsert en `search_index`.
   - `search-service/repositories/*.py` y `strategies/fuzzy_strategy.py` reescritos para leer de `search_index` en vez de `select(Song)`/`select(Album)`/`select(Artist)`.
   - **También se agregó indexado de artistas** (no estaba en el texto original de Fase 4, que solo mencionaba song/album): sin esto se perdía la búsqueda de artistas por nombre que ya existía. Se agregó `publish_artist_updated_event` en `artist-service/events/events.py` (antes solo existía `artist_created`).

2. **`artist_created`/`artist_updated` migrados a exchange fanout** (`artist-service/events/events.py`, `content-service/events/consumer.py`). Necesario porque ahora dos consumidores (content-service para el álbum "Sencillos" automático, y search-service para el índice) necesitan recibir el mismo evento — con la cola bare original se lo hubieran repartido entre sí en vez de recibirlo cada uno. `song_created/updated` y `album_created/updated` se dejaron en su patrón bare original (search-service es su único consumidor hoy, no hay conflicto). La migración completa de topología + DLQ para *todos* los eventos sigue siendo tarea de Fase 4.

3. **Bug de la Fase 1 encontrado y corregido de paso:** varios endpoints de lectura en `content-service` devolvían "no encontrado" como `200 OK` con body `{"status": "error", ...}` en vez de un 404 HTTP real (`error_response()` en vez de `HTTPException`). Esto rompía la detección de "no existe" para los nuevos llamadores internos (`InternalHTTPClient` distingue 404 de 5xx por status code). Se corrigió en los 3 endpoints de los que depende Fase 3: `GET /songs/{id}/enriched`, `GET /albums/{id}`, `DELETE /albums/artist/{id}`. El resto de endpoints de `content-service` (los que solo usa el frontend) se dejó igual — corregirlos todos es fuera de alcance de esta fase.

4. **Endpoint nuevo no listado explícitamente en el plan:** `DELETE /albums/artist/{artist_id}` en content-service. Necesario porque `artist-service/services/repositories/artist_repository.py` hacía cascade-delete manual de Album/Song/SongArtist al borrar un artista — con esas tablas ya no accesibles localmente, `artist-service` ahora llama a este endpoint antes de borrar su propio registro.

**Archivos nuevos:**
- `shared-python/vibestream_common/http_client.py` — `InternalHTTPClient` (get/post/delete sobre httpx.AsyncClient, distingue 404 de errores reales vía `InternalServiceError`).
- `auth-service/handlers/get_public_user.go` — `GET /users/:id` público.
- `search-service/events/consumer.py` y `search-service/events/__init__.py`.

**Pendiente antes de dar la fase por cerrada:**
- Correr `docker compose build --no-cache && docker compose up` en un equipo con Docker.
- Probar manualmente: registro de artista → álbum "Sencillos" automático → subir canción → crear playlist y agregar la canción (verificar enriquecimiento vía HTTP) → buscar por texto (canción, álbum y artista) → editar perfil de artista y confirmar que el índice de búsqueda se actualiza → eliminar un artista y confirmar que sus álbumes/canciones se borran en cascada vía el nuevo endpoint.
- Revisar en la UI de RabbitMQ (`localhost:15672`) que aparezcan los exchanges fanout `artist_created`/`artist_updated` con sus dos colas cada uno (`content_service.artist_created`/`search_service.artist_created`, etc.), y las colas bare `song_created`/`song_updated`/`album_created`/`album_updated` con search-service como consumidor.
- Si el volumen de Postgres/RabbitMQ ya existía de antes de este cambio: las colas bare `artist_created`/`artist_updated` viejas pueden quedar huérfanas (nada las consume ya, ver nota abajo). Para una demo/entrevista con `docker compose down -v` esto no aplica.

---

## Fase 4 — Limpieza de RabbitMQ

**Objetivo:** una sola topología de exchange consistente, DLQ, y una decisión explícita y justificada por servicio sobre si necesita eventos.

**Archivos:**
- Estandarizar en **exchange fanout** (ya correcto en `history-service/events/consumer.go` y `streaming-service/events/publisher.go`). Migrar `content-service/events/producer.py`/`consumer.py` y `artist-service/events/events.py` del patrón bare default-exchange a fanout con cola nombrada.
- Agregar DLQ: declarar un exchange `dlx` (fanout) + cola `dlq`, y en cada `declare_queue(...)` agregar `arguments={"x-dead-letter-exchange": "dlx"}`; los consumers usan `requeue=False` en vez de requeue infinito o drop silencioso.
- **search-service** — implementar `search-service/events/consumer.py` (nuevo, modelado sobre `content-service/events/consumer.py` pero ya con fanout+DLQ) consumiendo `song_created`/`song_updated`/`album_created`/`album_updated` de content-service para mantener su `search_index` local (la decisión CQRS confirmada). Wire-up en `search-service/main.py` con el mismo patrón `lifespan` que ya usa content-service.
- **playlist-service** y **subscription-service** — quitar `aio-pika` de `requirements.txt` (dependencia muerta hoy). Documentar explícitamente por qué: sus necesidades quedan resueltas con las llamadas HTTP síncronas de la Fase 3, y no hay un caso de uso real de evento asíncrono en el alcance actual — "lo evalué y decidí que no aplicaba" es una buena respuesta de entrevista.
- `content-service/events/consumer.py` — mantener el flujo real existente (artist-service publica `artist_created` → content-service crea álbum "Sencillos" automáticamente), solo migrarlo a fanout+DLQ.

**Verificación:**
- UI de management de RabbitMQ (`localhost:15672`) muestra un solo tipo de exchange para eventos de la app, más `dlx`/`dlq` visibles.
- Forzar una excepción en un consumer y confirmar que el mensaje termina en la DLQ, no desaparece ni hace loop.
- Crear un artista → confirmar que sigue creándose el álbum "Sencillos" (regresión).
- Crear/editar una canción en content-service → confirmar que el índice de search-service se actualiza sin query directa a la BD.

### ✅ Estado: implementada y verificada con Docker (2026-09-15)

**Cambios respecto al texto original del plan, decididos con el usuario durante la implementación:**

1. **Se agregó el alcance de eventos de borrado** (`artist_deleted`, `album_deleted`, `song_deleted`), no mencionado en el texto original de esta fase. Surgió como gap real encontrado durante la verificación de Fase 3: al eliminar un artista, sus álbumes/canciones se borraban en cascada en `content-service` pero `search_index` en search-service quedaba con entradas huérfanas (un usuario podía seguir "encontrando" por búsqueda un artista/canción ya eliminado). El usuario decidió explícitamente incorporar la corrección al alcance de esta fase en vez de dejarla como limitación aceptada.
   - `content-service/events/producer.py` — nuevos `publish_album_deleted_event`/`publish_song_deleted_event`.
   - `content-service/core/services/album_service.py` (`delete_album`) y `song_service.py` (`delete_song`) — publican el evento correspondiente tras el borrado (capturando el id *antes* del `commit()`, porque SQLAlchemy expira el objeto tras borrar+commitear y acceder a `.id` después dispara un refresh contra una fila que ya no existe).
   - `artist-service/events/events.py` — nuevo `publish_artist_deleted_event`; `artist-service/services/artist_service.py` (`delete_artist_by_user`) lo publica tras borrar localmente (mismo cuidado con capturar el id antes del delete).
   - `search-service/events/consumer.py` — nuevos handlers `handle_song_deleted`/`handle_album_deleted`/`handle_artist_deleted` que borran la fila de `search_index` por `(entity_type, entity_id)`.

2. **Estandarización a fanout se hizo total, incluyendo los eventos de borrado nuevos**, aunque hoy tengan un solo consumer (search-service) — se prefirió consistencia con el resto de la topología ("una sola topología de exchange consistente" del objetivo de esta fase) en vez de dejar una excepción bare-queue que habría que revisitar si aparece un segundo consumer.

3. **DLQ compartida implementada como paquete reusable en ambos lenguajes**, no solo como argumento repetido en cada `declare_queue`: `shared-python/vibestream_common/rabbitmq.py` (`declare_dlq`, `declare_fanout_queue`) y `shared-go/rabbitmq/dlq.go` (`DeclareDLQ`, `WorkQueueArgs`) — mismo exchange `dlx` (fanout) + cola `dlq`, un único punto de definición por lenguaje en vez de repetir la declaración en cada servicio.

4. **DLQ se extendió a `history-service`/`streaming-service` (Go)**, no mencionado explícitamente en el texto original de esta fase (que hablaba de DLQ en términos de `declare_queue` de Python). Se encontró que `history-service/events/consumer.go` hacía `d.Nack(false, true)` ante un error de procesamiento — **requeue infinito real**, exactamente el patrón que el objetivo de esta fase busca eliminar ("resulta en un 500 real y `requeue=false`"). Se cambió a `Nack(false, false)` con la cola `song_events_queue` configurada con `x-dead-letter-exchange`, en ambos lados (consumer y publisher deben declarar la cola con argumentos idénticos o RabbitMQ rechaza la segunda declaración).

5. **Bug real encontrado y corregido al verificar la migración a fanout de `song_created`/`album_created`:** los handlers de `search-service/events/consumer.py` capturaban `InternalServiceError` (fallo real de red/5xx llamando a content-service) y hacían `return` silencioso en vez de re-lanzar. Con `message.process()` de aio-pika, eso significa que el mensaje se **ACKeaba como exitoso** aunque el enriquecimiento hubiera fallado — el mismo "drop silencioso" que motivó esta fase, pero a nivel de lógica de negocio, no de configuración de cola. Se corrigió re-lanzando en el bloque `except InternalServiceError`, para que el mensaje se rechace y termine en la DLQ. **Confirmado experimentalmente**: se detuvo `content-service`, se publicó un `song_created` manualmente, y el mensaje apareció en `dlq` (antes de este fix se habría perdido sin dejar rastro).

**Verificación real ejecutada (Docker):**
- `docker compose build` (Go y Python afectados) + `go build ./...` en `shared-go`, `history-service`, `streaming-service`, `auth-service` — todo compila.
- RabbitMQ management API confirma: **9 exchanges fanout** de dominio (`artist_created/updated/deleted`, `album_created/updated/deleted`, `song_created/updated/deleted`) + `dlx`, y cada cola de trabajo con `x-dead-letter-exchange: dlx` en sus argumentos.
- Registrar artista → álbum "Sencillos" + indexado de ambos en `search_index` (regresión de Fase 3, sigue funcionando tras la migración bare→fanout).
- Eliminar artista → `search_index` queda limpio de artista y álbum (antes quedaban huérfanos — este es el gap que pediste incorporar a esta fase).
- DLQ real: `content-service` detenido → evento `song_created` publicado → falla el enriquecimiento (timeout) → mensaje aparece en `dlq` (1 mensaje) en vez de perderse.
- `playlist-service`/`subscription-service` arrancan sin `aio-pika` en `requirements.txt` (confirmado sin uso en ningún import antes de quitarlo).

**Nota operativa para quien reproduzca esto:** las colas bare viejas (`song_created`, `album_created`, etc.) y las colas nombradas de Fase 3 sin argumento DLQ (`search_service.artist_created`, `content_service.artist_created`) tuvieron que borrarse manualmente una vez (vía la management API) porque RabbitMQ rechaza redeclarar una cola existente con argumentos distintos (`PRECONDITION_FAILED`). En un `docker compose down -v` limpio (sin volumen persistente de RabbitMQ) esto no aplica — es solo relevante si se itera sobre un broker que ya tenía la topología vieja.

---

## Fase 5 — Base de testing y CI

**Objetivo:** pasar de cero tests/CI a una base mínima pero real — no cobertura completa, pero suficiente para que "¿por qué no hay tests?" nunca sea una pregunta incómoda.

**Archivos (1-2 tests de alto valor por servicio, no suites exhaustivas):**
- Go: `auth-service/services/auth_service_test.go` (login con los errores tipados de la Fase 1), `history-service/handlers/history_handler_test.go`, `streaming-service/handlers/stream_test.go`. Usar `testing` + `net/http/httptest` de la stdlib, sin framework externo.
- Python: un `tests/` por servicio con `pytest` + `pytest-asyncio` + `httpx.AsyncClient`/`TestClient` — ej. `playlist-service/tests/test_playlist_repository.py` cubriendo el fix de la Fase 1, `search-service/tests/test_fuzzy_strategy.py`. Nuevo `requirements-dev.txt` por servicio (sin tocar el `requirements.txt` de producción, que ya está bien pineado).
- `.golangci.yml` (uno por servicio Go o compartido en la raíz) con `govet`, `staticcheck`, `errcheck`, `gosimple`.
- `pyproject.toml` por servicio Python (o compartido) configurando `ruff`.
- `.github/workflows/ci.yml` en la raíz: un solo workflow con matrix job — para cada servicio Go, `go build && go vet && go test ./...` + `golangci-lint run`; para cada servicio Python, `pip install -r requirements.txt -r requirements-dev.txt`, `ruff check .`, `pytest`.

**Verificación:**
- `go test ./...` pasa en los 3 servicios Go localmente.
- `pytest` pasa en los 5 servicios Python localmente.
- Correr el workflow de GitHub Actions y confirmar verde en toda la matriz.
- Romper un test a propósito y confirmar que CI falla (prueba que el pipeline es real).

### ✅ Estado: implementada y verificada localmente (2026-09-15)

**Cambios respecto al texto original del plan:**

1. **`gosimple` no existe como linter separado en golangci-lint v2** (la versión actual) — sus reglas (S1xxx) se fusionaron dentro de `staticcheck`. `.golangci.yml` quedó con `govet`, `staticcheck`, `errcheck` — mismo alcance que pedía el plan, solo que consolidado. Confirmado corriendo `golangci-lint help linters` contra la imagen `golangci/golangci-lint:v2.1.6`.

2. **`ruff check` encontró errores reales en los 5 servicios Python** (no solo estilo): imports sin usar (`F401`) y orden de imports (`I001`) en código preexistente de toda la app, no solo en los archivos nuevos de esta fase. Se corrió `ruff check --fix .` una vez por servicio — es el mismo costo de adoptar un linter que correr `gofmt -w .` la primera vez sobre un repo Go: un fix mecánico, sin cambio de comportamiento, pero con un diff grande (~40 archivos, solo reordenamiento de imports). `E501` (línea larga) se dejó fuera de `select` en los 5 `pyproject.toml`: reformatear retroactivamente todas las líneas largas preexistentes no tenía valor funcional para el alcance de esta fase.

3. **El autofix de `ruff` rompió `content-service` de verdad**: `core/entities/album.py` importaba `SongOut` desde `core/entities/song` solo para re-exportarlo (un patrón frágil ya en el código original), y ruff lo marcó como "no usado" y lo borró — rompiendo el arranque del servicio (`ImportError` en `album_handler.py`, que importaba `SongOut` desde `core.entities.album` en vez de su módulo real). Encontrado recién al reconstruir y levantar el stack Docker completo después del autofix (exactamente por esto se verifica con Docker real, no solo con `pytest`). Corregido en la raíz: `album_handler.py` ahora importa `SongOut` desde `core.entities.song` directamente.

4. **Se corrigieron los hallazgos reales de `golangci-lint`** en vez de dejarlos para que el primer run de CI empezara en rojo: errores de retorno no chequeados (`errcheck`) en los 3 servicios Go, una rama `else` vacía, y un `SA4006` (valor nunca usado) en `history-service/main.go` que resultó ser **un bug de seguridad real**: la variable `allowedOrigins` se calculaba pero nunca se usaba — el CORS manual de ese archivo reflejaba *cualquier* header `Origin` del request con `Access-Control-Allow-Credentials: true`, ignorando el allowlist configurado. Este era justo el ítem que Fase 2 dejó pendiente ("reemplazar el CORS hecho a mano por `gin-contrib/cors`") y nunca se aplicó. Corregido migrando a `gin-contrib/cors`, igual que auth-service/streaming-service.

5. **`streaming-service/services/streaming_service.go` se eliminó** en vez de corregir sus lint issues: `grep` confirmó que `StreamingService`/`NewStreamingService` no se usaban en ningún otro archivo — la lógica de streaming real vive duplicada directamente en `handlers/stream.go`. Código muerto, no vale la pena mantenerlo lint-clean.

6. **Se agregaron 2 tests por servicio Python** en vez de solo los 2 ejemplos citados en el texto original (playlist-service, search-service) — el texto decía "un `tests/` por servicio", así que se completaron los 3 restantes:
   - `content-service`: regresión del bug de datetime de Fase 3 (`AlbumOut`/`SongOut`/`SongEnrichedOut` aceptan un `datetime` real) + `validate_album_ownership` (403 a no-dueños).
   - `artist-service`: la lista de excepciones públicas del `AuthMiddleware` (qué rutas quedan sin JWT) vía `TestClient`, incluyendo una regresión explícita del bug de Fase 3 (401 real, no 500).
   - `subscription-service`: reglas de negocio de `SubscriptionService` (no auto-suscribirse, no duplicar, artista inexistente).

7. **`shared-python/pyproject.toml` no declaraba `aio-pika`** como dependencia pese a que el nuevo `vibestream_common/rabbitmq.py` de Fase 4 lo importa — gap real encontrado al escribir los tests (no se manifestaba antes porque los 3 servicios que usan ese módulo ya tienen `aio-pika` en su propio `requirements.txt`, pero el paquete compartido en sí quedaba con una dependencia no declarada). Agregado a `dependencies`.

8. **Cada `conftest.py`/env var de test se documentó explícitamente**: los `Settings` de pydantic-settings se validan al importar `config.py`, así que cada servicio necesita variables dummy (`db_url_py`, `JWT_SECRET`, etc.) seteadas *antes* de que pytest importe cualquier módulo de la app — no estaba en el texto original del plan, es un detalle de implementación real de FastAPI/pydantic-settings.

**Verificación real ejecutada:**
- `go build && go vet && go test ./...` + `golangci-lint run` (contra `golangci/golangci-lint:v2.1.6`) — **0 issues** en los 3 servicios Go y en `shared-go`.
- `ruff check .` — **0 issues** en los 5 servicios Python, tras el fix.
- `python -m pytest tests/ -v` — **33 tests, todos pasan** (6 artist + 6 content + 9 playlist + 6 search + 6 subscription).
- **Se rompió un test a propósito** (Go y Python, uno de cada lado) y se confirmó que falla con el mensaje correcto, luego se revirtió — prueba de que el pipeline detecta regresiones reales, no que "siempre pasa".
- `docker compose build` (los 9 servicios) + `docker compose up` completo tras todos los cambios de esta fase (incluyendo el fix del bug de `ruff --fix` en content-service) — stack estable, 0 reinicios, smoke test manual de auth/history/streaming/content-service en verde.
- Nota: no se pudo correr el workflow de GitHub Actions real (`.github/workflows/ci.yml`) porque este entorno no tiene push a un remoto de GitHub — se simuló cada paso del workflow localmente contra los mismos comandos exactos (incluyendo el detalle real de `python -m pytest` vs `pytest` suelto, que si no se usa así rompe la resolución de imports locales en CI). **Pendiente real: confirmar en GitHub Actions una vez se haga push.**

---

## Fase 6 — Limpieza de Docker/Compose

**Objetivo:** endurecer la capa de contenedores y formalizar la gestión de schema, cerrando los hallazgos restantes de la auditoría.

**Archivos:**
- Los 5 Dockerfiles Python — agregar usuario no-root (`RUN adduser --disabled-password appuser && USER appuser`, igual que ya hacen bien los Dockerfiles Go) y build multi-stage real que no arrastre el toolchain de compilación a la imagen final.
- `auth-service/main.go`, `history-service/main.go` — agregar endpoint `/health` (falta hoy; los otros 6 servicios ya lo tienen).
- `HEALTHCHECK` en los 9 Dockerfiles (8 backend + frontend).
- `.dockerignore` por servicio (falta en los 9) excluyendo `__pycache__`, `.git`, `node_modules`, `.env`, tests.
- `docker-compose.yml` — reemplazar `RABBITMQ_DEFAULT_USER/PASS: guest/guest` hardcodeado por `${RABBITMQ_USER}`/`${RABBITMQ_PASS}` desde `.env`; agregar `restart: unless-stopped` a todos los servicios.
- Introducir **Alembic** para `content-service`, `artist-service` y una migración equivalente para `auth-service` (aunque sea Go, documentar explícitamente cómo se gestiona su migración — Alembic con modelo espejo o SQL crudo versionado, eligiendo una opción sin dejarlo ambiguo). `history-service` y `streaming-service` no necesitan tooling de migración propio bajo el nuevo modelo de propiedad — solo consumen el schema de otros, y esto se documenta como decisión explícita.
- `schema_reconstruido.sql` deja de ser el mecanismo de restauración manual y pasa a ser el punto de partida de las migraciones Alembic iniciales.

**Verificación:**
- `docker compose build` compila los Dockerfiles no-root multi-stage; `docker exec <contenedor> whoami` devuelve un usuario no-root en los 5 servicios Python.
- `docker compose ps` muestra `healthy` en los 9 servicios.
- `grep -n "guest" docker-compose.yml` → sin resultados.
- `alembic upgrade head` contra un Postgres limpio reproduce el schema de `schema_reconstruido.sql` para las tablas ya migradas.

### ✅ Estado: implementada y verificada con Docker (2026-09-16)

**Cambio de alcance decidido con el usuario durante la implementación:**

Preparando las migraciones de Alembic se encontró que **`content-service` todavía declaraba su propio modelo ORM `Artist` y hacía un join local a `artists`** para enriquecer canciones/álbumes (`song_repository.py`, `album_repository.py`) — contradiciendo la decisión de Fase 3 ("content-service deja de declarar su propio modelo Artist y la consulta vía HTTP") que el PLAN.md daba por implementada, aunque `schema_reconstruido.sql` ya documentaba esto como excepción conocida. El usuario decidió corregirlo dentro de esta fase en vez de diferirlo:

- **Nuevo endpoint `GET /artists/by-user/{user_id}`** en artist-service (público, mismo patrón que `GET /artists/{id}`) — content-service no tenía forma de resolver "artist_id del usuario autenticado" vía HTTP porque ese endpoint no existía.
- **`content-service/core/services/artist_lookup.py`** reescrito para llamar a artist-service vía `InternalHTTPClient` en vez de hacer `select(Artist.id)` local. Se mantuvo la firma `get_artist_id_by_user(user_id, db)` sin tocar sus ~7 call sites, aunque `db` ya no se use — documentado explícitamente en el docstring.
- **`content-service/infrastructure/db/models.py`** — eliminada la clase `Artist` completa; `Album.artist_id` y `song_artists.artist_id` dejan de tener FK física a `artists.id` (ya no había justificación para esa FK cross-servicio una vez removido el join que la necesitaba) y se validan vía HTTP en su lugar.
- **`SongEnrichedOut.from_song`** (`core/entities/song.py`) pasa a recibir `artist_name` ya resuelto (por el caller, vía el nuevo `ArtistLookupService.get_artist_name`) en vez de leerlo de una relación ORM local. Se eliminó el fallback a `song.artists[0]` (comprobado como código muerto en la práctica: todo song tiene `album_id`, y `album.artist_id` era ya la fuente preferida).
- **`AlbumRepository.get_albums_with_artist_info`** dejó de hacer `JOIN Artist`; `AlbumService.get_artist_albums_with_info` resuelve el `artist_name` con **una sola llamada HTTP** para todo el lote (todos los álbumes devueltos comparten el mismo `artist_id`), no N llamadas.
- **`SongRepository.list_by_artist`** se eliminó: dependía de la relación ORM `Song.artists` y `grep` confirmó que no lo llamaba nadie (código muerto real, no solo sospechado).
- **`SongRepository.add_artists`** (nuevo) inserta filas en `song_artists` directamente vía `insert()` de SQLAlchemy Core, reemplazando `song.artists.append(artist)` (que dependía de la relación ORM al `Artist` local eliminado).

Verificado con datos reales contra el stack Docker: registrar artista → álbum "Sencillos" → insertar canción → `GET /songs/{id}/enriched` y `GET /songs/batch` devuelven `artist_name` correcto vía HTTP → `GET /albums/my-albums` resuelve `artist_id` del usuario autenticado vía HTTP y `artist_name` del álbum vía HTTP → `PUT /albums/{id}` (ownership) acepta al dueño real y devuelve 403 a un usuario sin perfil de artista.

**Resto de la fase, según el texto original:**

1. **Dockerfiles Python reescritos a multi-stage real**: etapa `builder` con `build-essential` + un `venv` en `/opt/venv`; etapa `runtime` (`python:3.12.3-slim` limpio) copia solo el `venv` completo, sin arrastrar el compilador. Usuario no-root (`appuser`) vía `adduser --disabled-password --gecos ""`. Confirmado: `docker exec content-service whoami` → `appuser`.

2. **`/health` agregado a `auth-service` y `history-service`** (Go) — en `history-service` tuvo que registrarse *antes* de `r.Use(middleware.AuthMiddleware(...))` (que se aplica globalmente a todo lo registrado después), o habría quedado detrás de JWT como cualquier otra ruta.

3. **`HEALTHCHECK` en los 9 Dockerfiles.** Bug real encontrado al verificar: el healthcheck del frontend (`wget http://localhost/`) fallaba con "Connection refused" a pesar de que nginx sí estaba corriendo — `localhost` dentro del contenedor Alpine resuelve a `::1` (IPv6) primero y nginx solo escucha IPv4 (`listen 80;` sin `listen [::]:80;`). Corregido apuntando el healthcheck a `127.0.0.1` explícito. Los 9 servicios (+ RabbitMQ) muestran `healthy` en `docker compose ps`.

4. **`.dockerignore` por servicio**: dado que el build context de los 8 backends es la raíz del repo (`context: .` en `docker-compose.yml`, para poder copiar `shared-python`/`shared-go`), un `.dockerignore` único en la raíz no puede ser específico por servicio. Se usó el soporte de BuildKit para `<Dockerfile>.dockerignore` (uno junto a cada `Dockerfile`, con paths relativos al build context) — no mencionado en el texto original del plan, pero es la única forma de lograr "un `.dockerignore` por servicio" dado que todos comparten build context.

5. **`docker-compose.yml`**: `RABBITMQ_DEFAULT_USER/PASS` ahora leen `${RABBITMQ_USER}`/`${RABBITMQ_PASS}` de `.env` (default `guest`/`guest`, documentado en `.env.example` que hay que mantenerlos sincronizados con `RABBITMQ_URL` a mano — docker-compose no soporta variables derivadas de otras variables dentro de un mismo `.env`). `restart: unless-stopped` en los 9 servicios. Verificado en vivo: al reiniciar sin querer el Postgres de verificación durante esta sesión, `auth-service`/`history-service`/`streaming-service` (que fallan rápido si no hay DB al arrancar) se reiniciaron solos 6 veces hasta que la BD volvió a estar disponible, y luego quedaron estables — la política demostró su propósito real, no solo en teoría.

6. **Alembic para `content-service` y `artist-service`**, template async (`alembic init -t async`), con `settings.db_url` como única fuente de verdad para la URL de conexión (no duplicada en `alembic.ini`) y `alembic_version` dejada en el schema `public` a propósito (si viviera en `music_streaming`, Alembic necesitaría que ese schema ya existiera para crear su propia tabla de control, antes de correr la migración que lo crea). La migración inicial de cada servicio se probó de verdad contra un Postgres recién creado (no el de verificación, que ya tenía las tablas de `schema_reconstruido.sql`) — `alembic upgrade head` reprodujo el schema esperado en ambos, confirmado con `\d` contra la tabla real.

7. **auth-service (Go): SQL crudo versionado**, no Alembic con modelo espejo — decisión explícita, no ambigua. Introducir Alembic (Python) para un servicio Go habría significado mantener modelos SQLAlchemy sin ningún propósito en runtime, solo para tener algo que versionar; un archivo `.sql` numerado (`auth-service/migrations/0001_init_users_and_refresh_tokens.sql`) aplicado con `psql -f` es más simple y honesto sobre lo que realmente hace. Documentado explícitamente en el propio archivo el límite de este enfoque (no hay tabla de control tipo `alembic_version`) y cuándo migrar a `golang-migrate` si el número de migraciones crece. Verificado contra un Postgres limpio.

8. **`history-service`/`streaming-service` no tienen tooling de migración propio** — decisión explícita documentada en el encabezado actualizado de `schema_reconstruido.sql`: ambos solo consumen schema de otros servicios (`songs`, `play_history` inferida de SQL crudo sin modelo propio), no tienen tablas que gestionar.

9. **`schema_reconstruido.sql` actualizado** para reflejar su nuevo rol (punto de partida ya consumido por las migraciones, no mecanismo de restauración) y corregido para ya no mostrar las FKs físicas a `artists` que el refactor del punto de "Cambio de alcance" de arriba eliminó.

**Verificación real ejecutada:**
- `docker compose build` (9 imágenes) + `docker compose up` — 9 servicios + RabbitMQ en `healthy`, 0 reinicios inesperados (los 6 reinicios de auth/history/streaming fueron por la caída real del Postgres de verificación, no un bug).
- `docker exec content-service whoami` / `docker exec artist-service whoami` → `appuser` (no-root) en los 5 servicios Python.
- `grep -n "guest" docker-compose.yml` → solo aparece dentro de un comentario explicando el fix, no como valor hardcodeado.
- `alembic upgrade head` contra 2 instancias de Postgres limpias (una por servicio) reprodujo el schema esperado, confirmado columna por columna.
- Migración SQL de auth-service verificada igual, contra una tercera instancia limpia.
- Flujo funcional completo re-verificado end-to-end tras el refactor de artistas: registro → login → registro de artista → álbum automático → canción → enriquecimiento vía HTTP (song/album/batch) → ownership → todo en verde.
- `go build && go vet && go test ./...` + `golangci-lint run` — 0 issues en los 3 servicios Go tras los cambios de esta fase.
- `ruff check .` + `python -m pytest tests/ -v` — 0 issues, 34 tests pasan (7 artist + 6 content + 9 playlist + 6 search + 6 subscription — 1 más que al cierre de Fase 5, por el test nuevo del endpoint `by-user` de artist-service).

---

## Orden de fases — por qué este orden

0 → 1 → 2 → 3 → 4 → 5 → 6, porque:
- **0** es rápida y de riesgo cero — la más urgente de resolver.
- **1** antes de **2**: corregir la lógica de errores por servicio mientras es simple de revisar; la Fase 2 extrae código ya correcto en vez de extraer-y-luego-arreglar.
- **2** antes de **3**: el refactor de datos necesita el cliente HTTP y el manejo de errores compartido; y tocar el Dockerfile/build-context de cada servicio conviene hacerlo una sola vez.
- **3** antes de **4**: el diseño de eventos de search-service en la Fase 4 depende de que los endpoints/payloads de content-service de la Fase 3 ya estén definidos.
- **4** antes de **5**: no tiene sentido escribir tests contra una topología de RabbitMQ que está por cambiar.
- **5** antes de **6**: CI debe existir antes de tocar Docker, para que los cambios de Dockerfile de la Fase 6 queden validados por un build real en CI.
- **6** al final: es pulido operacional, más seguro de hacer una vez que el código ya está asentado.

---

## Post-Fase 6 — hallazgos al comparar contra el schema original real (2026-09-21)

El usuario aportó dos documentos con el schema original real (no reconstruido): `database_schemas.md` (columnas por tabla, leídas de la instancia Supabase real) y **`create_database.sql`** (el DDL completo — este es el que el usuario marcó como autoritativo por sobre el `.md` cuando difieren). Confirman que `music_streaming` es efectivamente el schema correcto (ninguna referencia a `music_stm`, el legacy en español, existe en el código — verificado con grep) y exponen hallazgos reales:

**Explícitamente descartado por el usuario: no se implementa módulo de analítica/dashboard.**
`create_database.sql` incluye 4 tablas de stats ya diseñadas (`song_stats`, `album_stats`, `artist_stats`, `daily_song_stats` — agregados mensuales/diarios de reproducciones) más 7 tablas de features adyacentes nunca construidas en el código (`now_playing`, `search_history`, `user_follows`, `user_likes`, `track_mood_features`, `mood_session_context`, `user_mood_settings` — recomendación por "mood"/IA). El usuario confirmó la intención original: en algún momento se planeó un dashboard por artista y analítica de usuarios, pero nunca se construyó — y decidió explícitamente **no implementarlo ahora**. Se deja anotado acá como backlog conocido, con el schema ya diseñado en `create_database.sql` por si se retoma en el futuro.

**Discrepancias reales encontradas, pendientes de decisión (no implementadas todavía):**

1. **`created_at`/`updated_at` de `artists`, `albums`, `songs`, `playlists` son `DATE` en el original**, no `TIMESTAMP`. Esta sesión (verificación de Fase 3) se había "corregido" Pydantic/SQLAlchemy de `date` a `datetime` en content-service y artist-service, asumiendo que `TIMESTAMP` era lo correcto — con este dato nuevo, esa corrección se alejó del diseño original. Además, `updated_at` no tiene default ni `onupdate` en el DDL real: se esperaba que la aplicación lo seteara explícitamente en cada UPDATE, no que Postgres lo calculara solo (lo que sí hacen hoy los modelos actuales vía `onupdate=CURRENT_TIMESTAMP`).
2. **`users.registerdate` es `DATE`**, no `TIMESTAMP` (`schema_reconstruido.sql` y la migración SQL de auth-service lo tienen como `TIMESTAMP`).
3. **`jwt.refresh_tokens.token` tiene `UNIQUE`** en el original; la migración actual no lo declara.
4. **`jwt.refresh_tokens.user_id` NO tiene FK física a `users`** en el original (`INTEGER NOT NULL` a secas); la migración actual sí la agregó (`REFERENCES ... ON DELETE CASCADE`).
5. **No existe ninguna tabla de unión playlist↔canción en `music_streaming`** en el original (solo existía en `music_stm`, la versión legacy en español). El `playlist_songs` que usa playlist-service hoy no es una reconstrucción de algo real — es algo que hubo que inventar porque la feature de playlists lo necesita y el schema "avanzado" nunca llegó a tener esa tabla. Vale la pena tenerlo presente como contexto (no es un error nuestro, es un hueco real del diseño original), no requiere acción.

**Resuelto por el usuario (2026-09-21):**

- **Punto 1 y 2 (DATE vs TIMESTAMP)**: el usuario decidió **usar TIMESTAMP**, es decir, mantener el comportamiento actual — no revertir el fix de esta sesión. No requirió cambios de código (ya estaba así).
- **Puntos 3 y 4 (jwt.refresh_tokens)**: el usuario aclaró que jwt "es solo una validación para usar las APIs" — se interpreta como decisión de **no tocar** `auth-service/migrations/0001_init_users_and_refresh_tokens.sql`; se mantiene el `UNIQUE` faltante y la FK física de más tal como están hoy.
- **Punto 5 (playlist_songs)**: el usuario pidió **empezar la implementación** alineando `playlists`/`playlist_songs` con `create_database.sql`. Implementado:
  - `playlist-service/database/models.py`: `Playlist` gana `cover_image`, `is_public`, `is_collaborative`, `total_songs`, `total_duration`, `follower_count`, `play_count`, `deleted_at` (columnas del original que faltaban); `created_at`/`updated_at` pasan de `Date` a `DateTime` (mismo criterio del punto 1). `PlaylistSong` gana `added_by` y `position`, tomados de la tabla equivalente de `music_stm.playlists_canciones` (`agregado_por`/`orden`) ya que `music_streaming` real no tiene ninguna tabla de unión playlist↔canción que copiar.
  - `duration_seconds` en `PlaylistSong` (agregado nuestro, no está en ningún original): snapshot de la duración al agregar la canción, para poder mantener `total_duration` sin pedirle de nuevo la canción a content-service al quitarla.
  - `total_songs`/`total_duration` se mantienen al vuelo en `add_song_to_playlist`/`remove_song_from_playlist` (repository). `follower_count`/`play_count` quedan como columnas con default 0 **sin lógica que las actualice** — necesitarían features que no existen (seguir una playlist, tracking de reproducciones) y son deuda adyacente a la analítica que el usuario decidió no implementar. `deleted_at` existe como columna pero `delete_playlist` sigue haciendo borrado físico — cambiar esa semántica es una decisión aparte, no implícita en agregar la columna.
  - `PlaylistRepository.get_playlist_song_rows` ahora ordena por `position` (las filas viejas sin posición asignada quedan al final, por `added_at`).
  - `database/dtos.py` se eliminó: código muerto (nada lo importaba, `playlist_handlers.py` ya tenía sus propios DTOs inline) que habría quedado desactualizado con estos cambios. La serialización `_playlist_to_dict` se centralizó en `services/playlist_service.py` (antes vivía duplicada en el handler).
  - `schema_reconstruido.sql` actualizado con el nuevo `CREATE TABLE` de `playlists`/`playlist_songs`.
  - 6 tests nuevos en `playlist-service/tests/test_playlist_repository.py` (mantenimiento de `total_songs`/`total_duration`, orden por `position`, `added_by`, actualización de los campos nuevos) — **14/14 pasan contra SQLite en memoria** (no se levantó Postgres/Docker Compose para esto, indicación explícita del usuario: "ya que no vamos a montar el proyecto... podés usar sqlite").

No se corrigieron (quedan tal cual, ver arriba): jwt.refresh_tokens (puntos 3-4).

---

## Post-Fase 6 — Postgres y LocalStack reales en docker-compose (2026-09-21)

Revisión completa pedida por el usuario ("¿falta algo?") encontró un problema activo real: el `playlist-service` corriendo en ese momento era de antes de los cambios de schema de la sección anterior, y el Postgres de verificación (un contenedor ad-hoc fuera de `docker-compose.yml`, usado desde Fase 3) todavía tenía el schema viejo de `playlists`/`playlist_songs` — reconstruir y redeployar con el código nuevo sin migrar la BD habría roto el servicio. El usuario pidió resolverlo montando Postgres en Docker de verdad, y de paso agregar LocalStack (ya instalado por el usuario, disponible vía Docker) para poder probar el flujo de S3 completo por primera vez en todo este trabajo — nunca se había podido ejercitar `POST /songs` con un archivo real, ni la subida de foto de perfil de artista, ni el streaming con soporte de `Range`, por falta de credenciales AWS.

**`docker-compose.yml` — 2 servicios nuevos:**
- `postgres` (postgres:16-alpine): bootstrapea con `schema_reconstruido.sql` completo vía `docker-entrypoint-initdb.d/` (mecanismo estándar de la imagen oficial: corre una sola vez, contra un volumen vacío). Esto resuelve el desincronizado de playlist-service de raíz — el schema ya incluido es el actualizado con `cover_image`/`is_public`/`total_songs`/etc. Nota documentada en el propio compose: Alembic (content-service, artist-service) gestiona el *drift incremental* a partir de acá, no el bootstrap inicial.
- `localstack` (localstack/localstack:3.8, `SERVICES=s3`): con un script de init (`localstack/init/01-create-bucket.sh`, usa `awslocal` — ya viene en la imagen, no hace falta instalarlo en el host) que crea el bucket automáticamente al arrancar.
- Los 8 servicios backend ganan `depends_on: postgres: condition: service_healthy`; los 3 que hablan con S3 (content-service, artist-service, streaming-service) ganan además `depends_on: localstack: condition: service_healthy`.
- 2 volúmenes nombrados nuevos: `postgres_data`, `localstack_data`.

**Código — soporte de endpoint S3 configurable (`AWS_ENDPOINT_URL`), sin tocar el comportamiento de AWS real cuando la variable no está seteada:**
- `content-service/config.py`, `artist-service/config.py`: `get_s3_client()` pasa `endpoint_url` + `Config(s3={"addressing_style": "path"})` a boto3 cuando `aws_endpoint_url` está seteado (LocalStack no resuelve virtual-hosted-style). `get_public_base_url()` idem.
- `content-service/infrastructure/storage/s3_client.py`: `build_s3_public_url`/`extract_s3_key_from_url` generan/reconocen ambos formatos de URL (AWS real y LocalStack) — esta es la función que realmente usan album/song_service (a diferencia de `settings.get_public_base_url()`, que resultó ser código muerto en content-service).
- `streaming-service/config/config.go`: nuevo campo `AWSEndpointURL`. `streaming-service/aws/s3.go`: `s3.NewFromConfig` con `BaseEndpoint`/`UsePathStyle` cuando corresponde. `streaming-service/utils/s3_utils.go`: `ExtractS3KeyFromURL` reconoce el formato LocalStack además del de AWS real.
- `.env`/`.env.example`: `POSTGRES_USER/PASSWORD/DB` (deben coincidir con `db_url_py`/`DB_URL`, mismo caso de "no hay variables derivadas" que RabbitMQ); `AWS_ENDPOINT_URL=http://localstack:4566` + credenciales dummy (`test`/`test`, LocalStack no las valida pero boto3/el SDK de Go exigen que no estén vacías).

**Verificado de punta a punta contra el stack real (primera vez para varios de estos flujos):**
- `docker compose up` desde cero: los 11 servicios (9 app + rabbitmq + postgres + localstack) quedan `healthy` sin intervención — el stack es autocontenido por primera vez (antes asumía una BD externa).
- Registro → login → registro de artista **con foto de perfil real subida a LocalStack** (`profile_pic` queda con URL `http://localstack:4566/vibestream-media/1/utils/profile_picture.png`, confirmado descargable) → álbum "Sencillos" automático → **`POST /songs` con archivo de audio real** (nunca antes probado en esta sesión completa) → `GET /songs/{id}/enriched` → **streaming real vía `GET /stream`, incluyendo `Range` header (200 con el archivo completo, 206 con contenido parcial exacto)** → crear playlist con los campos nuevos → agregar la canción (confirmado en la fila real de Postgres: `added_by`, `position`, `duration_seconds` todos correctos) → búsqueda encuentra la canción vía el pipeline real de eventos RabbitMQ.
- Iteración anterior a este bootstrap: se dio de baja el contenedor Postgres ad-hoc de verificación (`vibestream-postgres-verify`, usado desde Fase 3 por fuera de compose) y las redes Docker huérfanas que había generado — ya no hacen falta, `docker compose up` es autosuficiente.

**Pendiente real remanente:** el archivo de audio usado para la prueba de upload es un MP3 sintético mínimo (no un audio real), así que `mutagen` no pudo extraer duración/metadata real (`duration: 0`) — la lógica de extracción de metadata en sí no quedó ejercitada con un archivo de audio genuino, solo el pipeline de upload/storage/streaming alrededor de ella.
