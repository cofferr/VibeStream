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
