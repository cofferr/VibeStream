"""Manejo centralizado de errores compartido por los servicios FastAPI.

Provee el exception_handler global (patrón usado en artist-service desde
la Fase 1) y el decorador handle_errors para handlers que no pueden usar
un exception_handler global (p. ej. porque necesitan distinguir errores
de negocio con ValueError -> 400).
"""

import functools
import logging

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Error real de infraestructura/BD, distinto de un resultado vacío
    legítimo. Los repositorios deben lanzar esto en vez de devolver
    silenciosamente False/[]/0 en un except genérico."""


def make_global_exception_handler(cors_origin: str = "*"):
    """Crea un exception_handler global para FastAPI que loguea el error
    real server-side y devuelve un 500 saneado, preservando los headers
    de CORS en la respuesta de error."""

    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "Error no manejado en %s %s", request.method, request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers={
                "Access-Control-Allow-Origin": cors_origin,
                "Access-Control-Allow-Credentials": "true",
            },
        )

    return global_exception_handler


def handle_errors(func):
    """Decorador para handlers de FastAPI: loguea la excepción completa
    server-side y devuelve al cliente un mensaje genérico saneado,
    preservando los HTTPException ya lanzados intencionalmente."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            logger.exception("Error no manejado en %s", func.__name__)
            raise HTTPException(
                status_code=500, detail="Error interno del servidor"
            ) from e

    return wrapper
