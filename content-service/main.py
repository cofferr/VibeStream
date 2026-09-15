from config import settings
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from core.handlers.album_handler import router as album_router
from core.handlers.song_handler import router as song_router
from middleware.auth_middleware import AuthMiddleware
import asyncio
from contextlib import asynccontextmanager

try:
    from events.consumer import consume_events

    RABBITMQ_AVAILABLE = True
except ImportError:
    RABBITMQ_AVAILABLE = False
    print("[!] Módulo events.consumer no disponible")

import uvicorn
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(_):
    # Startup
    if RABBITMQ_AVAILABLE:
        try:
            task = asyncio.create_task(consume_events())
            print("[*] Consumer de artist_created iniciado en background.")
        except Exception as e:
            print(f"[!] Error iniciando consumer RabbitMQ: {e}")
            print("[!] Continuando sin RabbitMQ...")
    else:
        print("[!] Ejecutando sin RabbitMQ (modo desarrollo)")

    yield

    # Shutdown
    if "task" in locals():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("[*] Consumer detenido correctamente.")


app = FastAPI(title="Music Service", version="0.1", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.include_router(album_router)
app.include_router(song_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)

