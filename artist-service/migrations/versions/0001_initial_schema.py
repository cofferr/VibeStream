"""Schema inicial de artist-service: artists.

Fase 6: artist-service es dueño/escritor único de esta tabla (ver
PLAN.md, Fase 3). user_id no tiene FK física a music_streaming.users
(dueña: auth-service) — se valida en el registro/login de auth-service,
no como constraint de BD cross-servicio. Transcrito desde
database/models.py.

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
        "artists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("artist_name", sa.Text(), nullable=False, unique=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("profile_pic", sa.String(), nullable=True),
        sa.Column("social_links", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        schema="music_streaming",
    )
    op.create_index(
        "ix_artists_artist_name",
        "artists",
        ["artist_name"],
        schema="music_streaming",
    )


def downgrade() -> None:
    op.drop_table("artists", schema="music_streaming")
