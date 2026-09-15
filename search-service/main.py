import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from handlers.search_handler import router as search_router
from middleware.auth_middleware import AuthMiddleware
from config import settings
from vibestream_common.errors import make_global_exception_handler
import uvicorn

logger = logging.getLogger(__name__)

try:
    from events.consumer import consume_events

    RABBITMQ_AVAILABLE = True
except ImportError:
    RABBITMQ_AVAILABLE = False
    logger.warning("Módulo events.consumer no disponible")


@asynccontextmanager
async def lifespan(_):
    connection = None
    if RABBITMQ_AVAILABLE:
        try:
            connection = await consume_events()
        except Exception:
            logger.exception("Error iniciando consumer de search_index")
    else:
        logger.warning("Ejecutando sin RabbitMQ (search_index no se actualizará)")

    yield

    if connection is not None:
        await connection.close()


app = FastAPI(title="Search Service", version="0.1", lifespan=lifespan)

# configuración de CORS - DEBE IR PRIMERO
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware global
app.add_middleware(AuthMiddleware)

# Router de búsqueda
app.include_router(search_router, prefix="/search", tags=["Search"])


# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}


app.add_exception_handler(
    Exception,
    make_global_exception_handler(
        cors_origin=settings.frontend_origins[0]
        if settings.frontend_origins != ["*"]
        else "*"
    ),
)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)
