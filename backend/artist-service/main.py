import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from vibestream_common.errors import make_global_exception_handler

from config import settings
from handlers.artist_handler import router as artist_router
from middleware.auth_middleware import AuthMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(title="Artist Service", version="0.1")

# Configuración de CORS - DEBE IR PRIMERO
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar middleware de autenticación
app.add_middleware(AuthMiddleware)

# Rutas
app.include_router(artist_router, prefix="/artists", tags=["artists"])


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Manejo global de excepciones para asegurar headers CORS
app.add_exception_handler(
    Exception,
    make_global_exception_handler(
        cors_origin=settings.frontend_origins[0]
        if settings.frontend_origins != ["*"]
        else "*"
    ),
)


# Permitir ejecución directa con python3 main.py
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)

