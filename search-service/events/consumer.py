"""Consumer de eventos que mantiene actualizado el search_index local
(Fase 3/4: CQRS de búsqueda). Los eventos song_created/updated y
album_created/updated de content-service llevan solo ids, así que el
consumer llama a los endpoints enriquecidos de content-service para
obtener título/artista/portada antes de indexar — evita duplicar esa
lógica de enriquecimiento aquí y mantiene una sola fuente de verdad.
artist_created/updated se auto-contienen (ya traen artist_name).

Fase 4: todos los eventos usan exchange fanout + cola nombrada
(estandarizado, antes song/album usaban el exchange default de
RabbitMQ) y cada cola de trabajo declara la dead-letter-exchange
compartida (`vibestream_common.rabbitmq`) para no perder mensajes
fallidos en silencio. Los eventos *_deleted (nuevos en esta fase)
limpian la entrada correspondiente en vez de enriquecerla: sin esto,
borrar un artista/álbum/canción en content-service/artist-service
dejaba resultados de búsqueda huérfanos apuntando a contenido que ya
no existe."""

import asyncio
import json
import logging

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy import delete as sa_delete
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from vibestream_common.http_client import InternalHTTPClient, InternalServiceError
from vibestream_common.rabbitmq import declare_dlq, declare_fanout_queue

from config import settings
from database.connection import AsyncSessionLocal
from database.models import SearchIndexEntry

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


async def _delete_from_index(entity_type: str, entity_id: int) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            sa_delete(SearchIndexEntry).where(
                SearchIndexEntry.entity_type == entity_type,
                SearchIndexEntry.entity_id == entity_id,
            )
        )
        await session.commit()


def _parse_id(message: AbstractIncomingMessage, entity_label: str) -> int | None:
    data = json.loads(message.body.decode())
    entity_id = data.get("id")
    if not entity_id:
        logger.warning("Evento de %s inválido: falta id", entity_label)
    return entity_id


async def handle_song_event(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            song_id = _parse_id(message, "canción")
            if not song_id:
                return

            try:
                response = await content_client.get(f"/songs/{song_id}/enriched")
            except InternalServiceError:
                # Fallo real (5xx/timeout/red), no "no existe" (eso es un
                # 404 -> None, manejado abajo): re-lanzar para que el
                # mensaje termine en la DLQ en vez de ACKearse como si
                # hubiera indexado correctamente.
                logger.exception(
                    "No se pudo enriquecer canción %s desde content-service", song_id
                )
                raise

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
            raise


async def handle_song_deleted(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            song_id = _parse_id(message, "canción")
            if not song_id:
                return
            await _delete_from_index("song", song_id)
            logger.info("[✓] search_index: song %s eliminado", song_id)
        except json.JSONDecodeError:
            logger.error("Evento song_deleted inválido: no es JSON")
        except Exception:
            logger.exception("Error procesando evento song_deleted")
            raise


async def handle_album_event(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            album_id = _parse_id(message, "álbum")
            if not album_id:
                return

            try:
                response = await content_client.get(f"/albums/{album_id}")
            except InternalServiceError:
                logger.exception(
                    "No se pudo enriquecer álbum %s desde content-service", album_id
                )
                raise

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
            raise


async def handle_album_deleted(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            album_id = _parse_id(message, "álbum")
            if not album_id:
                return
            await _delete_from_index("album", album_id)
            logger.info("[✓] search_index: album %s eliminado", album_id)
        except json.JSONDecodeError:
            logger.error("Evento album_deleted inválido: no es JSON")
        except Exception:
            logger.exception("Error procesando evento album_deleted")
            raise


async def handle_artist_event(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
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
            raise


async def handle_artist_deleted(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            artist_id = _parse_id(message, "artista")
            if not artist_id:
                return
            await _delete_from_index("artist", artist_id)
            logger.info("[✓] search_index: artist %s eliminado", artist_id)
        except json.JSONDecodeError:
            logger.error("Evento artist_deleted inválido: no es JSON")
        except Exception:
            logger.exception("Error procesando evento artist_deleted")
            raise


# (exchange, cola propia de search-service, handler) — un solo lugar para
# ver toda la suscripción de eventos del servicio.
_SUBSCRIPTIONS = (
    ("song_created", "search_service.song_created", handle_song_event),
    ("song_updated", "search_service.song_updated", handle_song_event),
    ("song_deleted", "search_service.song_deleted", handle_song_deleted),
    ("album_created", "search_service.album_created", handle_album_event),
    ("album_updated", "search_service.album_updated", handle_album_event),
    ("album_deleted", "search_service.album_deleted", handle_album_deleted),
    ("artist_created", "search_service.artist_created", handle_artist_event),
    ("artist_updated", "search_service.artist_updated", handle_artist_event),
    ("artist_deleted", "search_service.artist_deleted", handle_artist_deleted),
)


async def consume_events():
    """Suscripción a todos los eventos que alimentan el search_index
    local, vía exchange fanout + cola propia por evento (Fase 4:
    topología consistente, antes song/album usaban el exchange default
    de RabbitMQ)."""
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    await declare_dlq(channel)

    for exchange_name, queue_name, handler in _SUBSCRIPTIONS:
        queue = await declare_fanout_queue(channel, exchange_name, queue_name)
        await queue.consume(handler)

    logger.info("[*] Esperando eventos para actualizar search_index...")
    return connection


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    connection = loop.run_until_complete(consume_events())
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(connection.close())
