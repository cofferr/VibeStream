import re

from config import settings
from fastapi import Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response
from vibestream_common.auth_middleware import AuthMiddleware as _BaseAuthMiddleware

# GET /artists/{id} es de solo lectura y la consumen content-service,
# search-service y subscription-service (Fase 3: propiedad de datos por
# servicio), que no tienen un JWT de usuario para reenviar.
_PUBLIC_GET_PATH_PATTERNS = (re.compile(r"^/artists/\d+$"),)


class AuthMiddleware(_BaseAuthMiddleware):
    def __init__(self, app):
        super().__init__(
            app,
            jwt_secret=settings.jwt_secret,
            jwt_algorithm=settings.jwt_algorithm,
            public_path_prefixes=("/health", "/files"),
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.method == "GET" and any(
            pattern.match(request.url.path) for pattern in _PUBLIC_GET_PATH_PATTERNS
        ):
            return await call_next(request)
        return await super().dispatch(request, call_next)
