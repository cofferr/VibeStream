import json
import aio_pika
from config import settings


async def publish_event(queue_name: str, payload: dict):
    """Función genérica para publicar eventos"""
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)

        message = aio_pika.Message(body=json.dumps(payload).encode())
        await channel.default_exchange.publish(message, routing_key=queue.name)


# -------------------------------
# Eventos específicos
# -------------------------------


async def publish_album_created_event(album_data: dict):
    await publish_event("album_created", album_data)


async def publish_album_updated_event(album_data: dict):
    await publish_event("album_updated", album_data)


async def publish_song_created_event(song_data: dict):
    await publish_event("song_created", song_data)


async def publish_song_updated_event(song_data: dict):
    await publish_event("song_updated", song_data)
