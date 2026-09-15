from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
import jwt

from config import settings

# claims requeridos según tu auth-service en Go
REQUIRED_CLAIMS = {"user_id", "username", "email", "role", "exp"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/health"):
            return await call_next(request)

        auth = HTTPBearer(auto_error=False)
        credentials = await auth(request)
        if credentials is None:
            raise HTTPException(status_code=401, detail="Falta header Authorization")

        token = credentials.credentials

        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                options={
                    "verify_signature": True,
                    "require": list(REQUIRED_CLAIMS),
                },
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidSignatureError:
            raise HTTPException(status_code=401, detail="Firma no válida")
        except jwt.MissingRequiredClaimError as e:
            raise HTTPException(status_code=400, detail=f"Falta claim: {e.claim}")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token inválido")

        request.state.user = {
            "user_id": payload["user_id"],
            "username": payload["username"],
            "email": payload["email"],
            "role": payload["role"],
        }

        return await call_next(request)
