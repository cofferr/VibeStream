"""Middleware de autenticación JWT compartido por los servicios FastAPI.

Consolida la lógica que estaba duplicada (y divergida) en cada servicio:
extraer el Bearer token, validar los claims requeridos, decodificar el
JWT y poblar request.state.user.

Los errores se devuelven como Response directamente (nunca `raise
HTTPException`): Starlette registra un handler pasado a
`add_exception_handler(Exception, ...)` como el `error_handler` de
`ServerErrorMiddleware`, que envuelve TODOS los middlewares de usuario
-incluido este-, no solo las rutas. Si este middleware lanzara
HTTPException, ese catch-all la interceptaría antes de llegar al
manejo específico de HTTPException de FastAPI, aplanando cualquier 401
en un 500 genérico. Devolver la Response acá evita ese problema y dejó
de ser un caso hipotético: se detectó verificando manualmente el flujo
de auth end-to-end contra un stack real (docker compose up).
"""

import logging
from typing import Iterable

import jwt
from fastapi import Request
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

REQUIRED_CLAIMS = {"user_id", "username", "email", "role", "exp"}

DEFAULT_PUBLIC_PATH_PREFIXES = ("/health",)


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        public_path_prefixes: Iterable[str] = DEFAULT_PUBLIC_PATH_PREFIXES,
        cors_origin: str = "*",
    ):
        super().__init__(app)
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.public_path_prefixes = tuple(public_path_prefixes)
        self.cors_origin = cors_origin

    def _error_response(self, status_code: int, detail: str) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={"detail": detail},
            headers={
                "Access-Control-Allow-Origin": self.cors_origin,
                "Access-Control-Allow-Credentials": "true",
            },
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path.startswith(self.public_path_prefixes):
            return await call_next(request)

        auth = HTTPBearer(auto_error=False)
        credentials = await auth(request)
        if credentials is None:
            return self._error_response(401, "Falta header Authorization")

        token = credentials.credentials

        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={
                    "verify_signature": True,
                    "require": list(REQUIRED_CLAIMS),
                },
            )
        except jwt.ExpiredSignatureError:
            return self._error_response(401, "Token expirado")
        except jwt.InvalidSignatureError:
            return self._error_response(401, "Firma no válida")
        except jwt.MissingRequiredClaimError as e:
            return self._error_response(400, f"Falta claim: {e.claim}")
        except jwt.InvalidTokenError:
            return self._error_response(401, "Token inválido")

        request.state.user = {
            "user_id": payload["user_id"],
            "username": payload["username"],
            "email": payload["email"],
            "role": payload["role"],
        }

        return await call_next(request)
