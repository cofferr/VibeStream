import json
import aio_pika  # librería async para RabbitMQ
from datetime import datetime, date
from config import settings


def default_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()  # convierte datetime/date a string ISO 8601
    raise TypeError(f"Type {type(obj)} not serializable")


async def publish_artist_created_event(artist_data: dict):
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        # Declaramos la cola (si no existe)
        queue = await channel.declare_queue("artist_created", durable=True)

        # Publicamos el mensaje, usando default_serializer para fechas
        message = aio_pika.Message(
            body=json.dumps(artist_data, default=default_serializer).encode()
        )
        await channel.default_exchange.publish(message, routing_key=queue.name)
