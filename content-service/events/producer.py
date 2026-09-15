import json

import aio_pika

from config import settings


async def publish_event(exchange_name: str, payload: dict):
    """Publica en un exchange fanout (Fase 4: topología consistente en
    toda la app). Antes usaba el exchange default de RabbitMQ con una
    cola declarada por nombre, lo que reparte los mensajes entre
    consumers en vez de duplicarlos — no era un problema mientras
    search-service era el único consumer, pero dejaba de serlo apenas
    un segundo servicio necesitara el mismo evento (como ya pasa con
    artist_created)."""
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            exchange_name, aio_pika.ExchangeType.FANOUT, durable=True
        )
        message = aio_pika.Message(body=json.dumps(payload).encode())
        await exchange.publish(message, routing_key="")


# -------------------------------
# Eventos específicos
# -------------------------------


async def publish_album_created_event(album_data: dict):
    await publish_event("album_created", album_data)


async def publish_album_updated_event(album_data: dict):
    await publish_event("album_updated", album_data)


async def publish_album_deleted_event(album_id: int):
    await publish_event("album_deleted", {"id": album_id})


async def publish_song_created_event(song_data: dict):
    await publish_event("song_created", song_data)


async def publish_song_updated_event(song_data: dict):
    await publish_event("song_updated", song_data)


async def publish_song_deleted_event(song_id: int):
    await publish_event("song_deleted", {"id": song_id})
