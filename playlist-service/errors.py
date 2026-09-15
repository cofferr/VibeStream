"""Manejo centralizado de errores para los handlers de playlist-service.

Evita repetir el mismo bloque try/except en cada endpoint y evita filtrar
el detalle interno de la excepción (str(e)) en la respuesta al cliente.
"""

import functools
import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Error real de infraestructura/BD, distinto de un resultado vacío
    legítimo. Los repositorios deben lanzar esto en vez de devolver
    silenciosamente False/[]/0 en un except genérico."""


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
