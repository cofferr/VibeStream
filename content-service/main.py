from config import settings
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from core.handlers.album_handler import router as album_router
from core.handlers.song_handler import router as song_router
from middleware.auth_middleware import AuthMiddleware
import asyncio
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

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


# Manejo global de excepciones para asegurar headers CORS
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Error no manejado en %s %s", request.method, request.url.path)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Credentials": "true",
        },
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)

