"""Consumer de eventos que mantiene actualizado el search_index local
(Fase 3/4: CQRS de búsqueda). Los eventos song_created/updated y
album_created/updated de content-service llevan solo ids, así que el
consumer llama a los endpoints enriquecidos de content-service para
obtener título/artista/portada antes de indexar — evita duplicar esa
lógica de enriquecimiento aquí y mantiene una sola fuente de verdad.
artist_created/updated se auto-contienen (ya traen artist_name)."""

import asyncio
import json
import logging

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from config import settings
from database.connection import AsyncSessionLocal
from database.models import SearchIndexEntry
from vibestream_common.http_client import InternalHTTPClient, InternalServiceError

logger = logging.getLogger(__name__)

content_client = InternalHTTPClient(settings.content_service_url)


async def _upsert(entity_type: str, entity_id: int, fields: dict) -> None:
    async with AsyncSessionLocal() as session:
        stmt = pg_insert(SearchIndexEntry).values(
            entity_type=entity_type, entity_id=entity_id, **fields
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_search_index_entity",
            set_={**fields, "updated_at": func.now()},
        )
        await session.execute(stmt)
        await session.commit()


async def handle_song_event(message: AbstractIncomingMessage) -> None:
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            song_id = data.get("id")
            if not song_id:
                logger.warning("Evento de canción inválido: falta id")
                return

            try:
                response = await content_client.get(f"/songs/{song_id}/enriched")
            except InternalServiceError:
                logger.exception(
                    "No se pudo enriquecer canción %s desde content-service", song_id
                )
                return

            song = (response or {}).get("data")
            if not song:
                logger.warning("Canción %s no encontrada en content-service", song_id)
                return

            await _upsert(
                "song",
                song_id,
                {
                    "title": song["title"],
                    "subtitle": song.get("artist_name"),
                    "cover_url": song.get("album_cover_url"),
                    "audio_url": song.get("audio_url"),
                    "artist_id": song.get("artist_id"),
                    "album_id": song.get("album_id"),
                    "duration": song.get("duration"),
                    "track_number": song.get("track_number"),
                },
            )
            logger.info("[✓] search_index actualizado para song %s", song_id)
        except json.JSONDecodeError:
            logger.error("Evento de canción inválido: no es JSON")
        except Exception:
            logger.exception("Error procesando evento de canción")


async def handle_album_event(message: AbstractIncomingMessage) -> None:
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            album_id = data.get("id")
            if not album_id:
                logger.warning("Evento de álbum inválido: falta id")
                return

            try:
                response = await content_client.get(f"/albums/{album_id}")
            except InternalServiceError:
                logger.exception(
                    "No se pudo enriquecer álbum %s desde content-service", album_id
                )
                return

            album = (response or {}).get("data")
            if not album:
                logger.warning("Álbum %s no encontrado en content-service", album_id)
                return

            await _upsert(
                "album",
                album_id,
                {
                    "title": album["title"],
                    "subtitle": None,
                    "cover_url": album.get("cover_url"),
                    "audio_url": None,
                    "artist_id": album.get("artist_id"),
                    "album_id": None,
                    "duration": None,
                    "track_number": None,
                },
            )
            logger.info("[✓] search_index actualizado para album %s", album_id)
        except json.JSONDecodeError:
            logger.error("Evento de álbum inválido: no es JSON")
        except Exception:
            logger.exception("Error procesando evento de álbum")


async def handle_artist_event(message: AbstractIncomingMessage) -> None:
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            artist_id = data.get("id")
            if not artist_id:
                logger.warning("Evento de artista inválido: falta id")
                return

            await _upsert(
                "artist",
                artist_id,
                {
                    "title": data.get("artist_name", ""),
                    "subtitle": None,
                    "cover_url": data.get("profile_pic"),
                    "audio_url": None,
                    "artist_id": artist_id,
                    "album_id": None,
                    "duration": None,
                    "track_number": None,
                },
            )
            logger.info("[✓] search_index actualizado para artist %s", artist_id)
        except json.JSONDecodeError:
            logger.error("Evento de artista inválido: no es JSON")
        except Exception:
            logger.exception("Error procesando evento de artista")


async def consume_events():
    """Suscripción a los eventos que alimentan el search_index local.

    song_created/updated y album_created/updated siguen el patrón bare de
    content-service (una sola cola, sin fanout: search-service es su único
    consumidor hoy). artist_created/updated usan fanout porque
    content-service también necesita recibir artist_created para su propio
    flujo (auto-creación del álbum 'Sencillos')."""
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()

    song_created_q = await channel.declare_queue("song_created", durable=True)
    await song_created_q.consume(handle_song_event)

    song_updated_q = await channel.declare_queue("song_updated", durable=True)
    await song_updated_q.consume(handle_song_event)

    album_created_q = await channel.declare_queue("album_created", durable=True)
    await album_created_q.consume(handle_album_event)

    album_updated_q = await channel.declare_queue("album_updated", durable=True)
    await album_updated_q.consume(handle_album_event)

    artist_created_exchange = await channel.declare_exchange(
        "artist_created", aio_pika.ExchangeType.FANOUT, durable=True
    )
    artist_created_q = await channel.declare_queue(
        "search_service.artist_created", durable=True
    )
    await artist_created_q.bind(artist_created_exchange)
    await artist_created_q.consume(handle_artist_event)

    artist_updated_exchange = await channel.declare_exchange(
        "artist_updated", aio_pika.ExchangeType.FANOUT, durable=True
    )
    artist_updated_q = await channel.declare_queue(
        "search_service.artist_updated", durable=True
    )
    await artist_updated_q.bind(artist_updated_exchange)
    await artist_updated_q.consume(handle_artist_event)

    logger.info("[*] Esperando eventos para actualizar search_index...")
    return connection


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    connection = loop.run_until_complete(consume_events())
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(connection.close())
