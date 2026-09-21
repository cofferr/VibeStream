-- ============================================================================
-- VibeStream — Schema de Postgres
-- ============================================================================
-- Un solo schema (music_streaming) más jwt para tokens de refresh. Cada
-- tabla tiene un único dueño/escritor (el servicio indicado en el
-- comentario de cada sección); el resto de los servicios la consume vía
-- HTTP interno o eventos de RabbitMQ, nunca con acceso directo a la
-- tabla de otro servicio.
--
-- Las FKs cross-servicio de abajo son "lógicas", no físicas: se validan
-- en el código de cada servicio (ver shared-python/vibestream_common/
-- http_client.py), no como constraint de base de datos. Es el trade-off
-- estándar de microservicios entre integridad referencial fuerte e
-- independencia real de despliegue por servicio — en este repo todos
-- los servicios comparten una sola instancia de Postgres por simplicidad
-- de desarrollo local, pero el código está escrito como si cada uno
-- tuviera la suya propia.
--
-- Propiedad por tabla (único escritor):
--   users, jwt.refresh_tokens           -> auth-service
--   artists                             -> artist-service
--   albums, songs, genres, song_artists -> content-service
--   artist_subscriptions                -> subscription-service
--   playlists, playlist_songs           -> playlist-service
--   search_index                        -> search-service (índice CQRS,
--       desnormalizado, se llena vía eventos RabbitMQ de content-service
--       y artist-service — ver search-service/events/consumer.py)
--   play_history                        -> history-service
--
-- content-service y artist-service gestionan su schema con Alembic
-- (ver <servicio>/migrations/versions/). auth-service (Go, sin ORM con
-- auto-migración) usa SQL versionado a mano en
-- auth-service/migrations/. Este archivo es el punto de partida para
-- ambos mecanismos y la única fuente de verdad para las tablas que
-- todavía no tienen migraciones formales (playlist-service,
-- subscription-service, search-service, history-service) — también es
-- el script que bootstrapea Postgres en docker-compose.yml.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS music_streaming;
CREATE SCHEMA IF NOT EXISTS jwt;

-- ============================================================================
-- IDENTIDAD (auth-service)
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
-- ARTISTAS (artist-service)
-- ============================================================================

CREATE TABLE music_streaming.artists (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL UNIQUE,  -- lógica, no física (users vive en auth-service)
    artist_name   VARCHAR NOT NULL UNIQUE,
    bio           TEXT,
    profile_pic   VARCHAR,
    social_links  JSON,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_artists_artist_name ON music_streaming.artists(artist_name);

-- ============================================================================
-- CATÁLOGO DE CONTENIDO (content-service)
-- artist_id en albums/song_artists es lógica, no física: content-service
-- resuelve/valida artistas vía HTTP a artist-service (ver
-- content-service/core/services/artist_lookup.py), sin mantener una
-- copia local de la tabla artists.
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
-- SUSCRIPCIONES (subscription-service)
-- user_id/artist_id lógicas: se validan vía GET /users/{id} (auth-service)
-- y GET /artists/{id} (artist-service) antes de insertar.
-- ============================================================================

CREATE TABLE music_streaming.artist_subscriptions (
    user_id     INTEGER NOT NULL,
    artist_id   INTEGER NOT NULL,
    created_at  DATE DEFAULT CURRENT_DATE,
    PRIMARY KEY (user_id, artist_id)
);

-- ============================================================================
-- PLAYLISTS (playlist-service)
-- user_id lógica (users vive en auth-service). playlist_songs.song_id
-- también es lógica: content-service valida su existencia
-- (GET /songs/{id}/enriched) antes de insertar, y el enriquecimiento
-- (título/artista/portada) se resuelve vía GET /songs/batch en vez de
-- un join local.
--
-- added_by/position no vienen de ningún original: se agregaron para
-- soportar orden explícito y atribución en playlists colaborativas.
-- duration_seconds es un snapshot de la duración al agregar la canción,
-- para poder mantener playlists.total_duration sin pedirle de nuevo la
-- canción a content-service al momento de quitarla.
--
-- follower_count/play_count existen como columnas pero sin lógica que
-- las actualice — necesitarían features que no están implementadas
-- (seguir una playlist, tracking de reproducciones). deleted_at existe
-- pero el borrado de playlist sigue siendo físico por ahora.
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
    follower_count    INTEGER NOT NULL DEFAULT 0,
    play_count        INTEGER NOT NULL DEFAULT 0,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at        TIMESTAMP
);

CREATE TABLE music_streaming.playlist_songs (
    playlist_id       INTEGER NOT NULL REFERENCES music_streaming.playlists(id),
    song_id           INTEGER NOT NULL,
    added_by          INTEGER,  -- user_id de quien la agregó, lógica (auth-service)
    position          INTEGER,
    duration_seconds  INTEGER,
    added_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (playlist_id, song_id)
);

-- ============================================================================
-- ÍNDICE DE BÚSQUEDA (search-service)
-- Índice local desnormalizado (CQRS): search-service no lee
-- songs/albums/artists directo, los mantiene acá vía eventos RabbitMQ de
-- content-service/artist-service — necesario porque hacer fuzzy
-- matching (rapidfuzz) sobre HTTP síncrono en cada búsqueda sería
-- demasiado lento.
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
-- ============================================================================

CREATE TABLE music_streaming.play_history (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES music_streaming.users(id),
    song_id    INTEGER NOT NULL REFERENCES music_streaming.songs(id),
    played_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_play_history_user_id_played_at
    ON music_streaming.play_history(user_id, played_at DESC);
