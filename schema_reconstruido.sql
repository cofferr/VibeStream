-- ============================================================================
-- VibeStream — Reconstrucción del schema Postgres a partir del código fuente
-- ============================================================================
-- Generado leyendo los modelos ORM reales de cada microservicio, ya que
-- NINGÚN servicio hace auto-migración (no hay AutoMigrate en Go ni
-- create_all()/Alembic en Python). El schema vivía solo en la base de datos
-- perdida, nunca versionado como código.
--
-- Fuente de verdad usada por tabla, cuando había versiones divergentes entre
-- servicios (varios servicios duplican modelos de tablas que no les
-- pertenecen):
--   - users, artists, albums, songs, genres, song_artists
--       -> content-service/infrastructure/db/models.py (la más completa:
--          tiene FKs con schema explícito, ondelete correcto, tabla Genre
--          real en vez de un genre_id suelto)
--   - artist_subscriptions -> subscription-service (única fuente)
--   - playlists, playlist_songs -> playlist-service (única fuente)
--   - play_history -> history-service (inferida de SQL crudo, ver nota abajo)
--   - jwt.refresh_tokens -> auth-service (única fuente)
--
-- NOTA IMPORTANTE sobre "users":
--   auth-service tiene la versión más completa y es el dueño lógico de
--   identidad (login/registro). Las columnas name/username/email/password/
--   role/birthdate vienen de ahí. artist-service, search-service y
--   playlist-service redefinen esta tabla con subconjuntos de columnas —
--   eso es deuda técnica del proyecto original, no algo que debas repetir,
--   pero para RESTAURAR datos existentes necesitas el superset de columnas,
--   que es este.
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
-- IDENTIDAD (auth-service es el dueño real; otros servicios solo leen)
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
-- CATÁLOGO DE CONTENIDO (content-service es el dueño real)
-- ============================================================================

CREATE TABLE music_streaming.artists (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL UNIQUE REFERENCES music_streaming.users(id),
    artist_name   VARCHAR NOT NULL UNIQUE,
    bio           TEXT,
    profile_pic   VARCHAR,
    social_links  JSON,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_artists_artist_name ON music_streaming.artists(artist_name);

CREATE TABLE music_streaming.genres (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR NOT NULL UNIQUE,
    description  TEXT
);
CREATE INDEX ix_genres_name ON music_streaming.genres(name);

CREATE TABLE music_streaming.albums (
    id            SERIAL PRIMARY KEY,
    artist_id     INTEGER NOT NULL REFERENCES music_streaming.artists(id) ON DELETE CASCADE,
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
    artist_id  INTEGER NOT NULL REFERENCES music_streaming.artists(id) ON DELETE CASCADE,
    PRIMARY KEY (song_id, artist_id)
);
CREATE UNIQUE INDEX ix_song_artists_song_id_artist_id
    ON music_streaming.song_artists(song_id, artist_id);

-- ============================================================================
-- SUSCRIPCIONES (subscription-service)
-- ============================================================================

CREATE TABLE music_streaming.artist_subscriptions (
    user_id     INTEGER NOT NULL REFERENCES music_streaming.users(id),
    artist_id   INTEGER NOT NULL REFERENCES music_streaming.artists(id),
    created_at  DATE DEFAULT CURRENT_DATE,
    PRIMARY KEY (user_id, artist_id)
);

-- ============================================================================
-- PLAYLISTS (playlist-service)
-- ============================================================================

CREATE TABLE music_streaming.playlists (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES music_streaming.users(id),
    name         VARCHAR NOT NULL,
    description  TEXT,
    created_at   DATE DEFAULT CURRENT_DATE,
    updated_at   DATE DEFAULT CURRENT_DATE
);

CREATE TABLE music_streaming.playlist_songs (
    playlist_id  INTEGER NOT NULL REFERENCES music_streaming.playlists(id),
    song_id      INTEGER NOT NULL REFERENCES music_streaming.songs(id),
    added_at     DATE DEFAULT CURRENT_DATE,
    PRIMARY KEY (playlist_id, song_id)
);

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
