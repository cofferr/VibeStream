"""Cliente HTTP interno compartido para llamadas service-to-service.

Envuelve httpx.AsyncClient para que los servicios que ya no tienen acceso
directo a las tablas de otro servicio (Fase 3: propiedad de datos por
servicio) puedan resolver/enriquecer datos vía su API HTTP interna, usando
los nombres DNS de Docker Compose (ej. http://content-service:8001).

Nota de entrevista: en producción real esto sería un cliente generado desde
un contrato (OpenAPI/gRPC) con reintentos y circuit breaker; aquí un wrapper
delgado de httpx es la elección pragmática dado el alcance del proyecto.
"""

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class InternalServiceError(Exception):
    """Error real llamando a otro servicio interno (red, timeout, 5xx)."""


class InternalHTTPClient:
    """Cliente delgado para llamar a otro microservicio por su base_url.

    Devuelve None en 404 (recurso no encontrado, caso legítimo) y lanza
    InternalServiceError en cualquier otra falla (timeout, conexión, 5xx),
    para que el llamador pueda distinguir "no existe" de "el servicio falló".
    """

    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get(self, path: str, params: Optional[dict] = None) -> Optional[Any]:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
        except httpx.HTTPError as e:
            logger.exception("Error llamando a servicio interno GET %s", url)
            raise InternalServiceError(f"Fallo al llamar a {url}") from e

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            logger.error(
                "Servicio interno respondió %s en GET %s: %s",
                response.status_code,
                url,
                response.text,
            )
            raise InternalServiceError(
                f"{url} respondió {response.status_code}"
            )
        return response.json()

    async def delete(self, path: str) -> Optional[Any]:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(url)
        except httpx.HTTPError as e:
            logger.exception("Error llamando a servicio interno DELETE %s", url)
            raise InternalServiceError(f"Fallo al llamar a {url}") from e

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            logger.error(
                "Servicio interno respondió %s en DELETE %s: %s",
                response.status_code,
                url,
                response.text,
            )
            raise InternalServiceError(
                f"{url} respondió {response.status_code}"
            )
        return response.json()

    async def post(self, path: str, json: Optional[dict] = None) -> Optional[Any]:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=json)
        except httpx.HTTPError as e:
            logger.exception("Error llamando a servicio interno POST %s", url)
            raise InternalServiceError(f"Fallo al llamar a {url}") from e

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            logger.error(
                "Servicio interno respondió %s en POST %s: %s",
                response.status_code,
                url,
                response.text,
            )
            raise InternalServiceError(
                f"{url} respondió {response.status_code}"
            )
        return response.json()
