-- ============================================================================
-- VibeStream — Reconstrucción del schema Postgres a partir del código fuente
-- ============================================================================
-- ESTADO (Fase 6): este archivo dejó de ser el mecanismo de restauración
-- manual del schema. content-service y artist-service ahora versionan su
-- schema con Alembic (ver <servicio>/migrations/versions/0001_initial_schema.py,
-- que transcribe las tablas de esos dos servicios de este archivo — sin la
-- FK física a artists que content-service tenía acá, eliminada en la
-- misma fase junto con el join local que la justificaba). auth-service
-- (Go, sin ORM con auto-migración) usa SQL versionado a mano en
-- auth-service/migrations/0001_init_users_and_refresh_tokens.sql, también
-- transcrito de acá. history-service y streaming-service no tienen
-- tooling de migración propio: solo consumen schema de otros servicios,
-- decisión explícita (ver PLAN.md, Fase 6). Las tablas de
-- subscription-service, playlist-service y search-service que siguen
-- abajo no tienen migraciones formales todavía — este archivo sigue
-- siendo su única fuente de verdad hasta que se les agregue Alembic.
--
-- Generado originalmente leyendo los modelos ORM reales de cada microservicio, ya que
-- NINGÚN servicio hace auto-migración (no hay AutoMigrate en Go ni
-- create_all()/Alembic en Python). El schema vivía solo en la base de datos
-- perdida, nunca versionado como código.
--
-- ACTUALIZADO en Fase 3 (refactor de propiedad de datos): antes de esta
-- fase, varios servicios declaraban su propio modelo ORM de tablas ajenas
-- (deuda técnica del proyecto original heredado). Fase 3 estableció un
-- único dueño/escritor por tabla; el resto consume esos datos vía HTTP
-- interno en vez de leer la tabla directo. Las FKs cross-schema de abajo
-- documentan la intención original del dato, pero ya NO existen como
-- constraint físico de BD — son "lógicas", aplicadas en el código de cada
-- servicio (ver vibestream_common/http_client.py). Eso es intencional: es
-- el trade-off estándar de microservicios entre integridad referencial
-- fuerte y independencia real de despliegue por servicio.
--
-- Propiedad final por tabla (único escritor):
--   - users, jwt.refresh_tokens          -> auth-service
--   - artists                            -> artist-service
--   - albums, songs, genres, song_artists -> content-service
--   - artist_subscriptions               -> subscription-service
--   - playlists, playlist_songs          -> playlist-service
--       (playlist_songs.song_id ya NO es FK a songs: solo guarda el id,
--        content-service es quien valida que la canción existe)
--   - search_index                       -> search-service
--       (índice local desnormalizado, CQRS: se llena vía eventos RabbitMQ
--        de content-service/artist-service, no con queries directas a sus
--        tablas — ver search-service/events/consumer.py)
--   - play_history                       -> history-service (inferida de
--        SQL crudo, ver nota abajo; no tocada por Fase 3)
--
-- NOTA IMPORTANTE sobre "users":
--   auth-service es el único dueño/escritor de esta tabla desde Fase 3.
--   Antes, artist-service, search-service y playlist-service también
--   declaraban su propio modelo ORM de esta tabla (subconjuntos de
--   columnas) — esa duplicación se eliminó; ahora leen los campos públicos
--   de un usuario vía GET /users/{id} en auth-service.
--
-- NOTA sobre play_history:
--   No existe ningún archivo de modelo (struct/clase) para esta tabla en
--   ningún servicio. history-service la usa con SQL crudo
--   (repositories/history_repository.go:20,35) pero nunca la declara ni
--   migra. La estructura de abajo es la mínima que satisface esas queries
--   (user_id, song_id, played_at) — si en producción tenía una PK propia u
--   otras columnas, ese detalle se perdió y no es recuperable del código.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS music_streaming;
CREATE SCHEMA IF NOT EXISTS jwt;

-- ============================================================================
-- IDENTIDAD (auth-service es el único dueño/escritor; otros servicios leen
-- vía GET /users/{id}, ya no con acceso directo a la tabla)
-- ============================================================================

CREATE TABLE music_streaming.users (
    id                     SERIAL PRIMARY KEY,
    name                   VARCHAR NOT NULL,
    username               VARCHAR NOT NULL UNIQUE,
    email                  VARCHAR NOT NULL UNIQUE,
    password               VARCHAR NOT NULL,           -- hash, no texto plano
    role                   VARCHAR NOT NULL DEFAULT 'user',
    birthdate              DATE,
    registerdate           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_username_change   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_email_change      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_password_change   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE jwt.refresh_tokens (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    token       VARCHAR NOT NULL,
    expires_at  TIMESTAMP NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ARTISTAS (artist-service es el único dueño/escritor desde Fase 3;
-- content-service/search-service/subscription-service leen vía
-- GET /artists/{id} en vez de acceso directo)
-- ============================================================================

CREATE TABLE music_streaming.artists (
    id            SERIAL PRIMARY KEY,
    -- user_id ya no es FK física a users (users vive en auth-service);
    -- se valida en el registro del artista vía llamada lógica, no constraint.
    user_id       INTEGER NOT NULL UNIQUE,
    artist_name   VARCHAR NOT NULL UNIQUE,
    bio           TEXT,
    profile_pic   VARCHAR,
    social_links  JSON,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_artists_artist_name ON music_streaming.artists(artist_name);

-- ============================================================================
-- CATÁLOGO DE CONTENIDO (content-service es el único dueño/escritor)
-- artist_id en albums/song_artists ya NO tiene FK física a artists
-- (Fase 6): content-service dejó de mantener su copia local de Artist
-- (join eliminado, resolvía título/nombre de artista en
-- SongEnrichedOut/get_artist_albums_with_info) y ahora resuelve/valida
-- artistas vía HTTP a artist-service (ver
-- content-service/core/services/artist_lookup.py). Antes de Fase 6 esta
-- FK era física porque ese join local la necesitaba; ya no aplica.
-- ============================================================================

CREATE TABLE music_streaming.genres (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR NOT NULL UNIQUE,
    description  TEXT
);
CREATE INDEX ix_genres_name ON music_streaming.genres(name);

CREATE TABLE music_streaming.albums (
    id            SERIAL PRIMARY KEY,
    artist_id     INTEGER NOT NULL,  -- lógica, no física (ver nota arriba)
    title         VARCHAR NOT NULL,
    release_date  DATE,
    cover_url     TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_albums_artist_id ON music_streaming.albums(artist_id);
CREATE INDEX ix_albums_title ON music_streaming.albums(title);

CREATE TABLE music_streaming.songs (
    id            SERIAL PRIMARY KEY,
    album_id      INTEGER REFERENCES music_streaming.albums(id) ON DELETE SET NULL,
    genre_id      INTEGER REFERENCES music_streaming.genres(id) ON DELETE SET NULL,
    title         VARCHAR NOT NULL,
    duration      INTEGER,          -- segundos
    audio_url     TEXT,
    track_number  INTEGER,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_songs_album_id ON music_streaming.songs(album_id);
CREATE INDEX ix_songs_genre_id ON music_streaming.songs(genre_id);
CREATE INDEX ix_songs_title ON music_streaming.songs(title);

CREATE TABLE music_streaming.song_artists (
    song_id    INTEGER NOT NULL REFERENCES music_streaming.songs(id) ON DELETE CASCADE,
    artist_id  INTEGER NOT NULL,  -- lógica, no física (ver nota arriba)
    PRIMARY KEY (song_id, artist_id)
);
CREATE UNIQUE INDEX ix_song_artists_song_id_artist_id
    ON music_streaming.song_artists(song_id, artist_id);

-- ============================================================================
-- SUSCRIPCIONES (subscription-service es el único dueño/escritor).
-- user_id/artist_id ya no son FK físicas: se validan vía GET /users/{id}
-- (auth-service) y GET /artists/{id} (artist-service) antes de insertar.
-- ============================================================================

CREATE TABLE music_streaming.artist_subscriptions (
    user_id     INTEGER NOT NULL,
    artist_id   INTEGER NOT NULL,
    created_at  DATE DEFAULT CURRENT_DATE,
    PRIMARY KEY (user_id, artist_id)
);

-- ============================================================================
-- PLAYLISTS (playlist-service es el único dueño/escritor).
-- user_id ya no es FK física a users. playlist_songs.song_id tampoco es FK
-- a songs: content-service valida su existencia (GET /songs/{id}/enriched)
-- antes de insertar, y el enriquecimiento (título/artista/portada) se
-- resuelve vía GET /songs/batch en vez de un join local — es el trade-off
-- estándar de microservicios entre integridad referencial fuerte e
-- independencia real de despliegue por servicio.
--
-- ACTUALIZADO post-Fase 6, contra create_database.sql (schema original
-- real aportado por el usuario 2026-09-21):
--   - created_at/updated_at pasan de DATE a TIMESTAMP (decisión
--     explícita del usuario — el original usaba DATE, se decidió
--     divergir a propósito).
--   - se agregan las columnas que playlists sí tenía en el original y
--     acá faltaban: cover_image, is_public, is_collaborative,
--     total_songs, total_duration, follower_count, play_count,
--     deleted_at. follower_count/play_count quedan sin lógica que las
--     actualice (necesitarían features que no existen: seguir una
--     playlist, tracking de reproducciones — deuda adyacente a
--     analítica, fuera de alcance). deleted_at existe pero
--     delete_playlist sigue haciendo borrado físico por ahora.
--   - playlist_songs NO existe en el music_streaming real (solo en
--     music_stm, la versión legacy en español, como
--     playlists_canciones) — se mantiene como algo que este servicio
--     necesita igual para que la feature funcione. added_by/position se
--     tomaron de esa tabla legacy (agregado_por/orden).
--     duration_seconds es un agregado nuestro (no está en ningún
--     original): guarda un snapshot de la duración al agregar la
--     canción para poder mantener playlists.total_duration sin pedirle
--     de nuevo la canción a content-service al momento de quitarla.
-- ============================================================================

CREATE TABLE music_streaming.playlists (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER NOT NULL,
    name              VARCHAR NOT NULL,
    description       TEXT,
    cover_image       TEXT,
    is_public         BOOLEAN NOT NULL DEFAULT TRUE,
    is_collaborative  BOOLEAN NOT NULL DEFAULT FALSE,
    total_songs       INTEGER NOT NULL DEFAULT 0,
    total_duration    INTEGER NOT NULL DEFAULT 0,
    follower_count    INTEGER NOT NULL DEFAULT 0,  -- sin lógica que lo actualice, ver nota arriba
    play_count        INTEGER NOT NULL DEFAULT 0,  -- sin lógica que lo actualice, ver nota arriba
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at        TIMESTAMP  -- columna presente, borrado sigue siendo físico por ahora
);

CREATE TABLE music_streaming.playlist_songs (
    playlist_id       INTEGER NOT NULL REFERENCES music_streaming.playlists(id),
    song_id           INTEGER NOT NULL,
    added_by          INTEGER,  -- user_id de quien la agregó, sin FK (users vive en auth-service)
    position          INTEGER,  -- NULL en filas de antes de este cambio
    duration_seconds  INTEGER,  -- snapshot, ver nota arriba
    added_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (playlist_id, song_id)
);

-- ============================================================================
-- ÍNDICE DE BÚSQUEDA (search-service es el único dueño/escritor)
-- Tabla nueva de Fase 3/4: search-service ya no lee songs/albums/artists
-- directo (esas tablas son de otros servicios). Mantiene este índice local
-- desnormalizado vía eventos RabbitMQ (song_created/updated,
-- album_created/updated de content-service; artist_created/updated de
-- artist-service) — patrón CQRS, necesario porque rapidfuzz sobre HTTP
-- síncrono por cada búsqueda sería demasiado lento.
-- ============================================================================

CREATE TABLE music_streaming.search_index (
    id           SERIAL PRIMARY KEY,
    entity_type  VARCHAR NOT NULL,  -- 'song' | 'album' | 'artist'
    entity_id    INTEGER NOT NULL,
    title        VARCHAR NOT NULL,
    subtitle     VARCHAR,           -- nombre del artista, cuando aplica
    cover_url    TEXT,
    audio_url    TEXT,
    artist_id    INTEGER,
    album_id     INTEGER,
    duration     INTEGER,
    track_number INTEGER,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Nombrada explícitamente porque el consumer hace upsert vía
    -- ON CONFLICT ON CONSTRAINT uq_search_index_entity (ver
    -- search-service/events/consumer.py) — debe coincidir con el nombre
    -- que genera SQLAlchemy en database/models.py.
    CONSTRAINT uq_search_index_entity UNIQUE (entity_type, entity_id)
);
CREATE INDEX ix_search_index_entity_type ON music_streaming.search_index(entity_type);
CREATE INDEX ix_search_index_entity_id ON music_streaming.search_index(entity_id);
CREATE INDEX ix_search_index_title ON music_streaming.search_index(title);

-- ============================================================================
-- HISTORIAL DE REPRODUCCIÓN (history-service)
-- Reconstruida de SQL crudo en history-service/repositories/history_repository.go
-- No hay modelo/struct para esta tabla en ningún archivo — estructura mínima
-- inferida de las queries INSERT/SELECT reales.
-- ============================================================================

CREATE TABLE music_streaming.play_history (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES music_streaming.users(id),
    song_id    INTEGER NOT NULL REFERENCES music_streaming.songs(id),
    played_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_play_history_user_id_played_at
    ON music_streaming.play_history(user_id, played_at DESC);
