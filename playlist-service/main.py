# main.py - VERSIÓN CORREGIDA
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from vibestream_common.errors import make_global_exception_handler

from config import settings
from handlers.playlist_handlers import router as playlist_router
from middleware.auth_middleware import AuthMiddleware

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Playlist Service",
    version="0.1",
    description="Microservicio para gestión de playlists de música",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ✅ MIDDLEWARE DE LOGGING PARA DEBUG (opcional pero útil)
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# ✅ CORS PRIMERO - Configuración corregida
logger.info(f"🌐 Configurando CORS con orígenes: {settings.frontend_origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ✅ AUTH MIDDLEWARE SEGUNDO
logger.info("🔐 Configurando AuthMiddleware")
app.add_middleware(AuthMiddleware)

# Router de playlists
app.include_router(playlist_router, prefix="/playlists", tags=["playlists"])

# Manejo global de excepciones no capturadas por @handle_errors (asegura
# headers CORS y body saneado también fuera de los handlers de ruta, p.
# ej. errores de middleware o de inyección de dependencias)
app.add_exception_handler(
    Exception,
    make_global_exception_handler(
        cors_origin=settings.frontend_origins[0]
        if settings.frontend_origins != ["*"]
        else "*"
    ),
)

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "playlist-service"}

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Playlist Service API",
        "version": "0.1",
        "docs": "/docs",
        "health": "/health",
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=settings.port, 
        reload=True,
        log_level="info"
    )