"""Middleware de autenticación JWT compartido por los servicios FastAPI.

Consolida la lógica que estaba duplicada (y divergida) en cada servicio:
extraer el Bearer token, validar los claims requeridos, decodificar el
JWT y poblar request.state.user. Los errores se propagan como
HTTPException para que el CORSMiddleware de FastAPI siga aplicando los
headers de CORS en la respuesta de error (antes cada servicio los
hardcodeaba a mano, algunos con un origen fijo distinto al configurado).
"""

import logging
from typing import Iterable

import jwt
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

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
    ):
        super().__init__(app)
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.public_path_prefixes = tuple(public_path_prefixes)

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
            raise HTTPException(status_code=401, detail="Falta header Authorization")

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
        except jwt.ExpiredSignatureError as e:
            raise HTTPException(status_code=401, detail="Token expirado") from e
        except jwt.InvalidSignatureError as e:
            raise HTTPException(status_code=401, detail="Firma no válida") from e
        except jwt.MissingRequiredClaimError as e:
            raise HTTPException(
                status_code=400, detail=f"Falta claim: {e.claim}"
            ) from e
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail="Token inválido") from e

        request.state.user = {
            "user_id": payload["user_id"],
            "username": payload["username"],
            "email": payload["email"],
            "role": payload["role"],
        }

        return await call_next(request)
