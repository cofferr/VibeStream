import re

from config import settings
from fastapi import Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response
from vibestream_common.auth_middleware import AuthMiddleware as _BaseAuthMiddleware

# Endpoints de solo lectura consumidos por otros servicios internos (Fase 3:
# propiedad de datos por servicio y Fase 4 adelantada: consumer de
# search-service), que no tienen un JWT de usuario para reenviar.
_PUBLIC_GET_PATH_PATTERNS = (
    re.compile(r"^/songs/\d+/enriched$"),
    re.compile(r"^/albums/\d+$"),
)
_PUBLIC_DELETE_PATH_PATTERNS = (re.compile(r"^/albums/artist/\d+$"),)


class AuthMiddleware(_BaseAuthMiddleware):
    def __init__(self, app):
        super().__init__(
            app,
            jwt_secret=settings.jwt_secret,
            jwt_algorithm=settings.jwt_algorithm,
            public_path_prefixes=("/health", "/files", "/songs/batch"),
            cors_origin=settings.frontend_origins[0]
            if settings.frontend_origins != ["*"]
            else "*",
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.method == "GET" and any(
            pattern.match(request.url.path) for pattern in _PUBLIC_GET_PATH_PATTERNS
        ):
            return await call_next(request)
        if request.method == "DELETE" and any(
            pattern.match(request.url.path) for pattern in _PUBLIC_DELETE_PATH_PATTERNS
        ):
            return await call_next(request)
        return await super().dispatch(request, call_next)
