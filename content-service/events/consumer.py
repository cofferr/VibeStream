import asyncio
import json

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from vibestream_common.rabbitmq import declare_dlq, declare_fanout_queue

from config import settings
from core.repositories.album_repository import AlbumRepository
from core.services.album_service import AlbumService
from core.services.artist_lookup import ArtistLookupService
from infrastructure.db.connection import AsyncSessionLocal

# Ya no se necesita crear estructura de carpetas local
# Todo se almacena en S3 con el formato: {artist_id}/{album_id}/{filename}


async def handle_artist_created(message: AbstractIncomingMessage) -> None:
    """Cuando se crea un artista, se crea automáticamente el álbum 'Sencillos' y su estructura de carpetas"""
    async with message.process(requeue=False):
        try:
            data = json.loads(message.body.decode())
            user_id = data.get("user_id")

            if not user_id:
                print("[!] Evento artist_created inválido: falta user_id")
                return

            # Abrimos sesión centralizada para todo el flujo
            async with AsyncSessionLocal() as session:
                # 🔹 Resolvemos artist_id usando la misma sesión
                artist_id = await ArtistLookupService.get_artist_id_by_user(
                    user_id, db=session
                )
                if not artist_id:
                    print(f"[!] No se pudo obtener artist_id para user_id {user_id}")
                    return

                repo = AlbumRepository(session)
                service = AlbumService(repo)

                # Nombre del álbum
                album_name = "Sencillos"

                # 🔹 Creamos el álbum y obtenemos el objeto completo
                album = await service.create_album(
                    album_name, user_id=user_id, db=session
                )

                # 🔹 Hacer commit explícito para asegurar que los cambios se persistan
                await session.commit()

            print(
                f"[✓] Álbum '{album_name}' (ID: {album.id}) y estructura de carpetas creados para usuario {user_id}, artist {artist_id}"
            )

        except json.JSONDecodeError:
            print("[!] Error: mensaje inválido (no es JSON)")
        except Exception as e:
            print(f"[!] Error procesando evento artist_created: {e}")


async def consume_events():
    """Suscripción a eventos de artistas vía exchange fanout: content-service
    y search-service consumen el mismo evento artist_created cada uno con su
    propia cola nombrada, para no repartirse los mensajes entre sí."""
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    await declare_dlq(channel)
    queue = await declare_fanout_queue(
        channel, "artist_created", "content_service.artist_created"
    )
    await queue.consume(handle_artist_created)
    print("[*] Esperando eventos artist_created...")
    return connection


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    connection = loop.run_until_complete(consume_events())
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(connection.close())
