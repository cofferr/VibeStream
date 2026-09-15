from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt
import time
from config import settings

REQUIRED_CLAIMS = {"user_id", "username", "email", "role", "exp"}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Permitir solicitudes OPTIONS (CORS preflight) sin autenticación
        if request.method == "OPTIONS":
            return await call_next(request)
            
        # Excluir rutas que no requieran autenticación
        if request.url.path.startswith("/health") or request.url.path.startswith("/files"):
            return await call_next(request)

        try:
            auth = HTTPBearer(auto_error=False)
            credentials = await auth(request)

            if credentials is None:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Falta header Authorization"},
                    headers={
                        "Access-Control-Allow-Origin": "http://localhost:5173",
                        "Access-Control-Allow-Credentials": "true",
                    }
                )

            token = credentials.credentials

            # Verificar expiración manualmente primero
            decoded_without_verify = jwt.decode(token, options={"verify_signature": False})
            exp = decoded_without_verify.get('exp')
            if exp and exp < time.time():
                raise jwt.ExpiredSignatureError("Token expirado")

            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                options={
                    "verify_signature": True,
                    "require": list(REQUIRED_CLAIMS),
                },
            )

            request.state.user = {
                "user_id": payload["user_id"],
                "username": payload["username"],
                "email": payload["email"],
                "role": payload["role"],
            }

            return await call_next(request)
            
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token expirado"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        except jwt.InvalidSignatureError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Firma no válida"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        except jwt.MissingRequiredClaimError as e:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Falta claim: {e.claim}"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        except jwt.InvalidTokenError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token inválido"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        except Exception as e:
            print(f"❌ Error inesperado en auth: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Error en autenticación"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )