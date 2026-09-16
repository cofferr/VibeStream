-- ============================================================================
-- auth-service — schema inicial (users, jwt.refresh_tokens)
-- ============================================================================
-- Fase 6: auth-service es Go y no tiene un ORM con auto-migración (no hay
-- AutoMigrate en el código, ver models/user.go y models/refresh_token.go).
-- Decisión explícita de esta fase, no ambigua: en vez de introducir
-- Alembic (Python) para gestionar el schema de un servicio Go — lo que
-- obligaría a mantener modelos SQLAlchemy espejo sin ningún propósito en
-- runtime, solo para tener algo que autogenerar — este servicio usa SQL
-- crudo versionado y numerado, aplicado manualmente:
--
--     psql "$DB_URL" -f auth-service/migrations/0001_init_users_and_refresh_tokens.sql
--
-- Futuras migraciones de este servicio se agregan como
-- 0002_<descripcion>.sql, 0003_<descripcion>.sql, etc., aplicadas en
-- orden. No hay tooling que registre qué migración ya corrió (no hay
-- tabla de control tipo alembic_version) — para un servicio con un solo
-- archivo de migración hasta ahora, agregar esa infraestructura sería
-- prematuro; se documenta como límite conocido de este enfoque, a
-- resolver (con golang-migrate u otra herramienta nativa de Go) si el
-- número de migraciones de este servicio crece.
--
-- Transcrito desde schema_reconstruido.sql. auth-service es el único
-- dueño/escritor de users y jwt.refresh_tokens (Fase 3).
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS music_streaming;
CREATE SCHEMA IF NOT EXISTS jwt;

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
