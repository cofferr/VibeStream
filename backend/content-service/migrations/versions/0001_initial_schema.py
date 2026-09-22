"""Schema inicial de content-service: genres, albums, songs, song_artists.

content-service es dueño/escritor único de estas 4 tablas. Ninguna
tiene FK física a music_streaming.artists (dueña: artist-service) — se
valida vía HTTP en tiempo de aplicación, no como constraint de BD (ver
core/services/artist_lookup.py). Transcrito desde create_database.sql,
que documenta la propiedad completa del schema y por qué las FKs
cross-servicio son "lógicas".

Revision ID: 0001
Revises:
Create Date: 2026-09-16
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS music_streaming")

    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("name"),
        schema="music_streaming",
    )
    op.create_index(
        "ix_genres_name", "genres", ["name"], schema="music_streaming"
    )

    op.create_table(
        "albums",
        sa.Column("id", sa.Integer(), primary_key=True),
        # Sin FK física a artists (Fase 6, ver docstring de este archivo)
        sa.Column("artist_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        schema="music_streaming",
    )
    op.create_index(
        "ix_albums_artist_id", "albums", ["artist_id"], schema="music_streaming"
    )
    op.create_index(
        "ix_albums_title", "albums", ["title"], schema="music_streaming"
    )

    op.create_table(
        "songs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "album_id",
            sa.Integer(),
            sa.ForeignKey("music_streaming.albums.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "genre_id",
            sa.Integer(),
            sa.ForeignKey("music_streaming.genres.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("audio_url", sa.Text(), nullable=True),
        sa.Column("track_number", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        schema="music_streaming",
    )
    op.create_index(
        "ix_songs_album_id", "songs", ["album_id"], schema="music_streaming"
    )
    op.create_index(
        "ix_songs_genre_id", "songs", ["genre_id"], schema="music_streaming"
    )
    op.create_index(
        "ix_songs_title", "songs", ["title"], schema="music_streaming"
    )

    op.create_table(
        "song_artists",
        sa.Column(
            "song_id",
            sa.Integer(),
            sa.ForeignKey("music_streaming.songs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        # Sin FK física a artists (Fase 6, ver docstring de este archivo)
        sa.Column("artist_id", sa.Integer(), primary_key=True),
        schema="music_streaming",
    )
    op.create_index(
        "ix_song_artists_song_id_artist_id",
        "song_artists",
        ["song_id", "artist_id"],
        unique=True,
        schema="music_streaming",
    )


def downgrade() -> None:
    op.drop_table("song_artists", schema="music_streaming")
    op.drop_table("songs", schema="music_streaming")
    op.drop_table("albums", schema="music_streaming")
    op.drop_table("genres", schema="music_streaming")
