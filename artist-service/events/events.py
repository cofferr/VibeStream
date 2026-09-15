import json
import aio_pika  # librería async para RabbitMQ
from datetime import datetime, date
from config import settings


def default_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()  # convierte datetime/date a string ISO 8601
    raise TypeError(f"Type {type(obj)} not serializable")


async def _publish(exchange_name: str, artist_data: dict):
    """Publica en un exchange fanout: content-service (auto-creación del
    álbum 'Sencillos') y search-service (indexado para búsqueda) necesitan
    recibir el mismo evento cada uno por su lado, lo que un exchange
    default de una sola cola no permite (repartiría los mensajes entre
    ambos en vez de duplicarlos)."""
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            exchange_name, aio_pika.ExchangeType.FANOUT, durable=True
        )

        message = aio_pika.Message(
            body=json.dumps(artist_data, default=default_serializer).encode()
        )
        await exchange.publish(message, routing_key="")


async def publish_artist_created_event(artist_data: dict):
    await _publish("artist_created", artist_data)


async def publish_artist_updated_event(artist_data: dict):
    """Mantiene actualizado el search_index de search-service cuando
    cambia el nombre/bio de un artista (Fase 3/4: CQRS de búsqueda)."""
    await _publish("artist_updated", artist_data)
