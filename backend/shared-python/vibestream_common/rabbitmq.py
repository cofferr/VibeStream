"""Topología de RabbitMQ compartida (Fase 4).

Antes de esta fase, un consumer que fallaba en procesar un mensaje lo
perdía silenciosamente: `message.process()` de aio-pika hace
`reject(requeue=False)` por default ante una excepción no manejada, y
sin una dead-letter-exchange configurada en la cola, un mensaje
rechazado se descarta sin dejar rastro (se confirmó este comportamiento
verificando manualmente el flujo real: un álbum publicado antes de un
fix de un bug de serialización desapareció de la cola sin llegar nunca
a `search_index`, sin ningún error visible).

Un único DLX (`dlx`, fanout) + una única cola `dlq` centralizan esos
mensajes fallidos de toda la app en vez de perderlos. Cualquier cola de
trabajo debe declararse con `arguments=QUEUE_ARGS` para enrutar sus
rechazos ahí, y quien la declare primero (productor o consumer, según
quién arranque antes) debe llamar `declare_dlq(channel)` para que el
exchange/cola existan antes de que se intente enrutar nada hacia ellos.
"""

import aio_pika
from aio_pika.abc import AbstractChannel

DLX_EXCHANGE = "dlx"
DLQ_QUEUE = "dlq"
QUEUE_ARGS = {"x-dead-letter-exchange": DLX_EXCHANGE}


async def declare_dlq(channel: AbstractChannel) -> None:
    """Declara el exchange `dlx` (fanout, durable) y la cola `dlq`
    enlazada a él. Idempotente: seguro de llamar desde cada servicio que
    declare colas de trabajo, sin coordinación entre ellos."""
    exchange = await channel.declare_exchange(
        DLX_EXCHANGE, aio_pika.ExchangeType.FANOUT, durable=True
    )
    queue = await channel.declare_queue(DLQ_QUEUE, durable=True)
    await queue.bind(exchange)


async def declare_fanout_queue(
    channel: AbstractChannel, exchange_name: str, queue_name: str
):
    """Declara un exchange fanout + una cola nombrada enlazada a él, con
    los argumentos de DLQ ya aplicados. Patrón repetido por cada
    consumer de un evento de dominio (artist_created, song_deleted,
    etc.): cada servicio interesado se suscribe con su propia cola
    nombrada para no repartirse los mensajes entre sí."""
    exchange = await channel.declare_exchange(
        exchange_name, aio_pika.ExchangeType.FANOUT, durable=True
    )
    queue = await channel.declare_queue(
        queue_name, durable=True, arguments=QUEUE_ARGS
    )
    await queue.bind(exchange)
    return queue
