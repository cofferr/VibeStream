-- =============================================================
-- MusicStreaming Database — DDL completo
-- Esquemas: jwt | music_stm | music_streaming
-- =============================================================

-- ─────────────────────────────────────────────────────────────
-- CREAR ESQUEMAS
-- ─────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS jwt;
CREATE SCHEMA IF NOT EXISTS music_stm;
CREATE SCHEMA IF NOT EXISTS music_streaming;


-- =============================================================
-- ESQUEMA: jwt
-- =============================================================

CREATE TABLE jwt.refresh_tokens (
    id          SERIAL          PRIMARY KEY,
    user_id     INTEGER         NOT NULL,
    token       VARCHAR         NOT NULL UNIQUE,
    expires_at  TIMESTAMP       NOT NULL,
    created_at  TIMESTAMP       NOT NULL DEFAULT NOW()
);


-- =============================================================
-- ESQUEMA: music_stm  (versión inicial — nombres en español)
-- =============================================================

-- ── Usuarios ─────────────────────────────────────────────────
CREATE TABLE music_stm.usuarios (
    id_usuarios             SERIAL          PRIMARY KEY,
    nombre_usuario          VARCHAR(100)    NOT NULL,
    email                   VARCHAR(150)    NOT NULL UNIQUE,
    password_hash           TEXT            NOT NULL,
    rol                     TEXT            NOT NULL DEFAULT 'usuario',
    fecha_nacimiento        DATE,
    fecha_registro          TIMESTAMP       NOT NULL DEFAULT NOW(),
    last_email_change       TIMESTAMPTZ,
    last_password_change    TIMESTAMPTZ,
    username                VARCHAR(50)     UNIQUE,
    last_username_change    TIMESTAMPTZ
);

-- ── Géneros ──────────────────────────────────────────────────
CREATE TABLE music_stm.generos (
    id_generos  SERIAL          PRIMARY KEY,
    nombre      VARCHAR(50)     NOT NULL UNIQUE
);

-- ── Artistas ─────────────────────────────────────────────────
CREATE TABLE music_stm.artistas (
    id_artistas         SERIAL  PRIMARY KEY,
    id_usuario          INTEGER NOT NULL REFERENCES music_stm.usuarios(id_usuarios) ON DELETE CASCADE,
    nombre_artistico    VARCHAR(45) NOT NULL,
    biografia           TEXT
);

-- ── Álbumes ──────────────────────────────────────────────────
CREATE TABLE music_stm.albumes (
    id_albumes          SERIAL          PRIMARY KEY,
    titulo              VARCHAR(45)     NOT NULL,
    fecha_lanzamiento   DATE,
    portada_url         TEXT,
    creado_en           TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- ── Canciones ────────────────────────────────────────────────
CREATE TABLE music_stm.canciones (
    id_canciones        SERIAL  PRIMARY KEY,
    titulo              VARCHAR NOT NULL,
    duracion            INTEGER,           -- segundos
    url_audio           TEXT    NOT NULL,
    fecha_publicacion   DATE
);

-- ── Géneros de canciones (relación N:M) ──────────────────────
CREATE TABLE music_stm.canciones_generos (
    canciones_id    INTEGER NOT NULL REFERENCES music_stm.canciones(id_canciones) ON DELETE CASCADE,
    genero_id       INTEGER NOT NULL REFERENCES music_stm.generos(id_generos)     ON DELETE CASCADE,
    PRIMARY KEY (canciones_id, genero_id)
);

-- ── Artistas por álbum (N:M) ─────────────────────────────────
CREATE TABLE music_stm.albumes_artistas (
    id_albumes_artistas SERIAL  PRIMARY KEY,
    album_id            INTEGER NOT NULL REFERENCES music_stm.albumes(id_albumes)   ON DELETE CASCADE,
    artista_id          INTEGER NOT NULL REFERENCES music_stm.artistas(id_artistas) ON DELETE CASCADE,
    rol                 VARCHAR(50)
);

-- ── Canciones por álbum (N:M ordenado) ───────────────────────
CREATE TABLE music_stm.albumes_canciones (
    id_albumes_canciones    SERIAL      PRIMARY KEY,
    album_id                INTEGER     NOT NULL REFERENCES music_stm.albumes(id_albumes)   ON DELETE CASCADE,
    cancion_id              INTEGER     NOT NULL REFERENCES music_stm.canciones(id_canciones) ON DELETE CASCADE,
    orden                   INTEGER,
    nota                    VARCHAR(255),
    creado_en               TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ── Artistas por canción (N:M) ────────────────────────────────
CREATE TABLE music_stm.artistas_canciones (
    id_artistas_canciones   SERIAL  PRIMARY KEY,
    artista_id              INTEGER NOT NULL REFERENCES music_stm.artistas(id_artistas)  ON DELETE CASCADE,
    canciones_id            INTEGER NOT NULL REFERENCES music_stm.canciones(id_canciones) ON DELETE CASCADE,
    rol                     VARCHAR(50)
);

-- ── Playlists ─────────────────────────────────────────────────
CREATE TABLE music_stm.playlists (
    id_playlists            SERIAL      PRIMARY KEY,
    usuario_id              INTEGER     NOT NULL REFERENCES music_stm.usuarios(id_usuarios) ON DELETE CASCADE,
    nombre                  VARCHAR(50) NOT NULL,
    descripcion             TEXT,
    fecha_creacion          TIMESTAMP   NOT NULL DEFAULT NOW(),
    fecha_actualizacion     TIMESTAMP,
    es_publica              BOOLEAN     NOT NULL DEFAULT TRUE,
    es_colaborativa         BOOLEAN     NOT NULL DEFAULT FALSE
);

-- ── Canciones en playlist ─────────────────────────────────────
CREATE TABLE music_stm.playlists_canciones (
    id_playlists_canciones  SERIAL      PRIMARY KEY,
    playlist_id             INTEGER     NOT NULL REFERENCES music_stm.playlists(id_playlists)  ON DELETE CASCADE,
    cancion_id              INTEGER     NOT NULL REFERENCES music_stm.canciones(id_canciones)   ON DELETE CASCADE,
    agregado_por            INTEGER     REFERENCES music_stm.usuarios(id_usuarios),
    posicion                INTEGER,
    fecha_agregado          TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ── Colaboradores de playlist ─────────────────────────────────
CREATE TABLE music_stm.playlists_colaboradores (
    playlist_id INTEGER     NOT NULL REFERENCES music_stm.playlists(id_playlists) ON DELETE CASCADE,
    usuario_id  INTEGER     NOT NULL REFERENCES music_stm.usuarios(id_usuarios)   ON DELETE CASCADE,
    agregado_en TIMESTAMP   NOT NULL DEFAULT NOW(),
    PRIMARY KEY (playlist_id, usuario_id)
);

-- ── Seguidores de playlist ────────────────────────────────────
CREATE TABLE music_stm.playlists_seguidores (
    playlist_id         INTEGER     NOT NULL REFERENCES music_stm.playlists(id_playlists) ON DELETE CASCADE,
    usuario_id          INTEGER     NOT NULL REFERENCES music_stm.usuarios(id_usuarios)   ON DELETE CASCADE,
    fecha_seguimiento   TIMESTAMP   NOT NULL DEFAULT NOW(),
    PRIMARY KEY (playlist_id, usuario_id)
);

-- ── Historial de reproducciones ───────────────────────────────
CREATE TABLE music_stm.historial_reproducciones (
    id_historial_reproducciones SERIAL      PRIMARY KEY,
    usuario_id                  INTEGER     NOT NULL REFERENCES music_stm.usuarios(id_usuarios)   ON DELETE CASCADE,
    cancion_id                  INTEGER     NOT NULL REFERENCES music_stm.canciones(id_canciones)  ON DELETE CASCADE,
    fecha_reproduccion          TIMESTAMP   NOT NULL DEFAULT NOW(),
    duracion_reproducida        INTEGER,   -- segundos escuchados
    completada                  BOOLEAN     NOT NULL DEFAULT FALSE
);

-- ── Estadísticas de reproducciones ───────────────────────────
CREATE TABLE music_stm.estadisticas_reproducciones (
    id_estadisticas_reproducciones  SERIAL      PRIMARY KEY,
    usuario_id                      INTEGER     NOT NULL REFERENCES music_stm.usuarios(id_usuarios)   ON DELETE CASCADE,
    cancion_id                      INTEGER     NOT NULL REFERENCES music_stm.canciones(id_canciones)  ON DELETE CASCADE,
    reproducciones                  INTEGER     NOT NULL DEFAULT 0,
    ultima_reproduccion             TIMESTAMP,
    tiempo_total                    INTEGER     NOT NULL DEFAULT 0  -- segundos acumulados
);

-- ── Feedbacks ─────────────────────────────────────────────────
CREATE TABLE music_stm.feedbacks (
    id_feedbacks    SERIAL      PRIMARY KEY,
    usuario_id      INTEGER     NOT NULL REFERENCES music_stm.usuarios(id_usuarios) ON DELETE CASCADE,
    entity_type     VARCHAR     NOT NULL,   -- 'cancion', 'album', 'playlist', etc.
    entity_id       INTEGER     NOT NULL,
    feedback_type   VARCHAR     NOT NULL,   -- 'like', 'dislike', 'report', etc.
    creado_en       TIMESTAMP   NOT NULL DEFAULT NOW()
);


-- =============================================================
-- ESQUEMA: music_streaming  (versión avanzada — inglés + IA)
-- =============================================================

-- ── Users ─────────────────────────────────────────────────────
CREATE TABLE music_streaming.users (
    id                      SERIAL          PRIMARY KEY,
    name                    VARCHAR         NOT NULL,
    username                VARCHAR(50)     UNIQUE NOT NULL,
    email                   VARCHAR(150)    UNIQUE NOT NULL,
    password                VARCHAR         NOT NULL,
    role                    VARCHAR(20)     NOT NULL DEFAULT 'user',
    birthdate               DATE,
    registerdate            DATE            NOT NULL DEFAULT CURRENT_DATE,
    last_username_change    TIMESTAMP,
    last_email_change       TIMESTAMP,
    last_password_change    TIMESTAMP,
    profile_picture         TEXT,
    bio                     TEXT,
    last_login              TIMESTAMP,
    deleted_at              TIMESTAMP                             -- soft delete
);

-- ── Genres ────────────────────────────────────────────────────
CREATE TABLE music_streaming.genres (
    id          SERIAL  PRIMARY KEY,
    name        VARCHAR NOT NULL UNIQUE,
    description TEXT
);

-- ── Artists ───────────────────────────────────────────────────
CREATE TABLE music_streaming.artists (
    id                  SERIAL      PRIMARY KEY,
    user_id             INTEGER     NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    artist_name         TEXT        NOT NULL,
    bio                 TEXT,
    profile_pic         VARCHAR,
    banner_pic          TEXT,
    social_links        JSON,
    total_followers     INTEGER     NOT NULL DEFAULT 0,
    total_plays         INTEGER     NOT NULL DEFAULT 0,
    monthly_listeners   INTEGER     NOT NULL DEFAULT 0,
    is_verified         BOOLEAN     NOT NULL DEFAULT FALSE,
    verified_at         TIMESTAMP,
    created_at          DATE        NOT NULL DEFAULT CURRENT_DATE,
    updated_at          DATE,
    deleted_at          TIMESTAMP
);

-- ── Albums ────────────────────────────────────────────────────
CREATE TABLE music_streaming.albums (
    id              SERIAL          PRIMARY KEY,
    artist_id       INTEGER         NOT NULL REFERENCES music_streaming.artists(id) ON DELETE CASCADE,
    title           VARCHAR         NOT NULL,
    release_date    DATE,
    cover_url       TEXT,
    album_type      VARCHAR(20)     DEFAULT 'album',  -- album, single, EP, etc.
    total_tracks    INTEGER         NOT NULL DEFAULT 0,
    total_plays     INTEGER         NOT NULL DEFAULT 0,
    total_likes     INTEGER         NOT NULL DEFAULT 0,
    created_at      DATE            NOT NULL DEFAULT CURRENT_DATE,
    updated_at      DATE,
    deleted_at      TIMESTAMP
);

-- ── Songs ─────────────────────────────────────────────────────
CREATE TABLE music_streaming.songs (
    id              SERIAL      PRIMARY KEY,
    album_id        INTEGER     NOT NULL REFERENCES music_streaming.albums(id)  ON DELETE CASCADE,
    genre_id        INTEGER     REFERENCES music_streaming.genres(id),
    title           VARCHAR     NOT NULL,
    duration        INTEGER,            -- segundos
    audio_url       TEXT        NOT NULL,
    track_number    INTEGER,
    disc_number     INTEGER     DEFAULT 1,
    bitrate         INTEGER,
    sample_rate     INTEGER,
    file_size       BIGINT,
    file_format     VARCHAR,
    lyrics          TEXT,
    has_lyrics      BOOLEAN     NOT NULL DEFAULT FALSE,
    play_count      INTEGER     NOT NULL DEFAULT 0,
    like_count      INTEGER     NOT NULL DEFAULT 0,
    skip_count      INTEGER     NOT NULL DEFAULT 0,
    is_explicit     BOOLEAN     NOT NULL DEFAULT FALSE,
    is_available    BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      DATE        NOT NULL DEFAULT CURRENT_DATE,
    updated_at      DATE,
    deleted_at      TIMESTAMP
);

-- ── Song Artists (N:M) ────────────────────────────────────────
CREATE TABLE music_streaming.song_artists (
    song_id     INTEGER NOT NULL REFERENCES music_streaming.songs(id)   ON DELETE CASCADE,
    artist_id   INTEGER NOT NULL REFERENCES music_streaming.artists(id) ON DELETE CASCADE,
    PRIMARY KEY (song_id, artist_id)
);

-- ── Playlists ─────────────────────────────────────────────────
CREATE TABLE music_streaming.playlists (
    id              SERIAL      PRIMARY KEY,
    user_id         INTEGER     NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    name            VARCHAR     NOT NULL,
    description     TEXT,
    cover_image     TEXT,
    is_public       BOOLEAN     NOT NULL DEFAULT TRUE,
    is_collaborative BOOLEAN   NOT NULL DEFAULT FALSE,
    total_songs     INTEGER     NOT NULL DEFAULT 0,
    total_duration  INTEGER     NOT NULL DEFAULT 0,    -- segundos
    follower_count  INTEGER     NOT NULL DEFAULT 0,
    play_count      INTEGER     NOT NULL DEFAULT 0,
    created_at      DATE        NOT NULL DEFAULT CURRENT_DATE,
    updated_at      DATE,
    deleted_at      TIMESTAMP
);

-- ── Artist Subscriptions ──────────────────────────────────────
CREATE TABLE music_streaming.artist_subscriptions (
    user_id     INTEGER NOT NULL REFERENCES music_streaming.users(id)   ON DELETE CASCADE,
    artist_id   INTEGER NOT NULL REFERENCES music_streaming.artists(id) ON DELETE CASCADE,
    created_at  DATE    NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (user_id, artist_id)
);

-- ── User Follows ──────────────────────────────────────────────
CREATE TABLE music_streaming.user_follows (
    follower_id     INTEGER     NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    following_id    INTEGER     NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    followed_at     TIMESTAMP   NOT NULL DEFAULT NOW(),
    PRIMARY KEY (follower_id, following_id),
    CHECK (follower_id <> following_id)
);

-- ── User Likes ────────────────────────────────────────────────
CREATE TABLE music_streaming.user_likes (
    id          SERIAL      PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    entity_type VARCHAR     NOT NULL,   -- 'song', 'album', 'playlist', 'artist'
    entity_id   INTEGER     NOT NULL,
    liked_at    TIMESTAMP   NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, entity_type, entity_id)
);

-- ── Song Stats (mensuales) ────────────────────────────────────
CREATE TABLE music_streaming.song_stats (
    id              SERIAL      PRIMARY KEY,
    song_id         INTEGER     NOT NULL REFERENCES music_streaming.songs(id)   ON DELETE CASCADE,
    year            INTEGER     NOT NULL,
    month           INTEGER     NOT NULL CHECK (month BETWEEN 1 AND 12),
    play_count      INTEGER     NOT NULL DEFAULT 0,
    total_play_count INTEGER    NOT NULL DEFAULT 0,
    updated_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    UNIQUE (song_id, year, month)
);

-- ── Album Stats (mensuales) ───────────────────────────────────
CREATE TABLE music_streaming.album_stats (
    id              SERIAL      PRIMARY KEY,
    album_id        INTEGER     NOT NULL REFERENCES music_streaming.albums(id)  ON DELETE CASCADE,
    year            INTEGER     NOT NULL,
    month           INTEGER     NOT NULL CHECK (month BETWEEN 1 AND 12),
    play_count      INTEGER     NOT NULL DEFAULT 0,
    total_play_count INTEGER    NOT NULL DEFAULT 0,
    updated_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    UNIQUE (album_id, year, month)
);

-- ── Artist Stats (mensuales) ──────────────────────────────────
CREATE TABLE music_streaming.artist_stats (
    id              SERIAL      PRIMARY KEY,
    artist_id       INTEGER     NOT NULL REFERENCES music_streaming.artists(id) ON DELETE CASCADE,
    year            INTEGER     NOT NULL,
    month           INTEGER     NOT NULL CHECK (month BETWEEN 1 AND 12),
    play_count      INTEGER     NOT NULL DEFAULT 0,
    total_play_count INTEGER    NOT NULL DEFAULT 0,
    updated_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    UNIQUE (artist_id, year, month)
);

-- ── Daily Song Stats ──────────────────────────────────────────
CREATE TABLE music_streaming.daily_song_stats (
    id                      BIGSERIAL   PRIMARY KEY,
    song_id                 INTEGER     NOT NULL REFERENCES music_streaming.songs(id) ON DELETE CASCADE,
    date                    DATE        NOT NULL,
    total_plays             INTEGER     NOT NULL DEFAULT 0,
    total_skips             INTEGER     NOT NULL DEFAULT 0,
    total_likes             INTEGER     NOT NULL DEFAULT 0,
    unique_listeners        INTEGER     NOT NULL DEFAULT 0,
    total_duration_played   BIGINT      NOT NULL DEFAULT 0,
    avg_completion_rate     DOUBLE PRECISION,
    created_at              TIMESTAMP   NOT NULL DEFAULT NOW(),
    UNIQUE (song_id, date)
);

-- ── Now Playing ───────────────────────────────────────────────
CREATE TABLE music_streaming.now_playing (
    id                  SERIAL      PRIMARY KEY,
    user_id             INTEGER     NOT NULL UNIQUE REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    song_id             INTEGER     NOT NULL REFERENCES music_streaming.songs(id),
    position            INTEGER     NOT NULL DEFAULT 0,    -- segundos
    is_playing          BOOLEAN     NOT NULL DEFAULT FALSE,
    volume              INTEGER     NOT NULL DEFAULT 100,
    repeat_mode         VARCHAR     NOT NULL DEFAULT 'none',  -- none, one, all
    shuffle_enabled     BOOLEAN     NOT NULL DEFAULT FALSE,
    queue_context       VARCHAR,       -- 'album', 'playlist', 'artist', etc.
    queue_context_id    INTEGER,
    started_at          TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ── Search History ────────────────────────────────────────────
CREATE TABLE music_streaming.search_history (
    id              BIGSERIAL   PRIMARY KEY,
    user_id         INTEGER     NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    query           TEXT        NOT NULL,
    result_count    INTEGER,
    searched_at     TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ── Track Mood Features (IA de mood) ─────────────────────────
CREATE TABLE music_streaming.track_mood_features (
    id                  SERIAL          PRIMARY KEY,
    song_id             INTEGER         NOT NULL UNIQUE REFERENCES music_streaming.songs(id) ON DELETE CASCADE,
    primary_mood        VARCHAR(50),
    secondary_mood      VARCHAR(50),
    tempo               DOUBLE PRECISION,
    energy              DOUBLE PRECISION CHECK (energy BETWEEN 0 AND 1),
    valence             DOUBLE PRECISION CHECK (valence BETWEEN 0 AND 1),
    danceability        DOUBLE PRECISION CHECK (danceability BETWEEN 0 AND 1),
    acousticness        DOUBLE PRECISION CHECK (acousticness BETWEEN 0 AND 1),
    instrumentalness    DOUBLE PRECISION CHECK (instrumentalness BETWEEN 0 AND 1),
    mood_tags           JSON,
    mood_confidence     DOUBLE PRECISION CHECK (mood_confidence BETWEEN 0 AND 1),
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP
);

-- ── Mood Session Context ──────────────────────────────────────
CREATE TABLE music_streaming.mood_session_context (
    id                      SERIAL      PRIMARY KEY,
    user_id                 INTEGER     NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    current_dominant_mood   VARCHAR(50),
    recent_track_ids        JSON,
    playback_context_type   VARCHAR(50),
    context_id              INTEGER,
    session_start           TIMESTAMP   NOT NULL DEFAULT NOW(),
    last_updated            TIMESTAMP   NOT NULL DEFAULT NOW(),
    is_active               BOOLEAN     NOT NULL DEFAULT TRUE
);

-- ── User Mood Settings ────────────────────────────────────────
CREATE TABLE music_streaming.user_mood_settings (
    id                      SERIAL      PRIMARY KEY,
    user_id                 INTEGER     NOT NULL UNIQUE REFERENCES music_streaming.users(id) ON DELETE CASCADE,
    mood_ai_enabled         BOOLEAN     NOT NULL DEFAULT TRUE,
    transition_smoothness   VARCHAR,   -- 'soft', 'moderate', 'sharp', etc.
    last_toggle_at          TIMESTAMP,
    created_at              TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP
);


-- =============================================================
-- ÍNDICES RECOMENDADOS
-- =============================================================

-- jwt
CREATE INDEX idx_refresh_tokens_user_id ON jwt.refresh_tokens(user_id);

-- music_stm
CREATE INDEX idx_ms_historial_usuario    ON music_stm.historial_reproducciones(usuario_id);
CREATE INDEX idx_ms_historial_cancion    ON music_stm.historial_reproducciones(cancion_id);
CREATE INDEX idx_ms_estadisticas_usuario ON music_stm.estadisticas_reproducciones(usuario_id);
CREATE INDEX idx_ms_playlists_usuario    ON music_stm.playlists(usuario_id);

-- music_streaming
CREATE INDEX idx_songs_album_id          ON music_streaming.songs(album_id);
CREATE INDEX idx_songs_genre_id          ON music_streaming.songs(genre_id);
CREATE INDEX idx_albums_artist_id        ON music_streaming.albums(artist_id);
CREATE INDEX idx_artists_user_id         ON music_streaming.artists(user_id);
CREATE INDEX idx_user_likes_user_id      ON music_streaming.user_likes(user_id);
CREATE INDEX idx_search_history_user_id  ON music_streaming.search_history(user_id);
CREATE INDEX idx_daily_song_stats_date   ON music_streaming.daily_song_stats(song_id, date);
CREATE INDEX idx_mood_session_user       ON music_streaming.mood_session_context(user_id, is_active);
CREATE INDEX idx_now_playing_user        ON music_streaming.now_playing(user_id);
