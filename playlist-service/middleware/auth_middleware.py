# middleware/auth_middleware.py - VERSIÓN CORREGIDA
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import jwt
import logging
from config import settings

logger = logging.getLogger(__name__)

# claims requeridos según tu auth-service en Go
REQUIRED_CLAIMS = {"user_id", "username", "email", "role", "exp"}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # ✅ PERMITIR OPTIONS requests sin autenticación (CORS preflight)
        if request.method == "OPTIONS":
            logger.debug("OPTIONS request - skipping auth")
            return await call_next(request)
        
        # ✅ PERMITIR endpoints públicos sin autenticación
        public_paths = [
            "/health", 
            "/", 
            "/docs", 
            "/redoc", 
            "/openapi.json",
            "/favicon.ico"
        ]
        
        if any(request.url.path == path or request.url.path.startswith(path + '/') for path in public_paths):
            logger.debug(f"Public path {request.url.path} - skipping auth")
            return await call_next(request)

        # ✅ INICIALIZAR request.state.user como None por defecto
        if not hasattr(request.state, 'user'):
            request.state.user = None

        auth = HTTPBearer(auto_error=False)
        credentials = await auth(request)
        
        if credentials is None:
            logger.warning("Missing Authorization header")
            raise HTTPException(status_code=401, detail="Falta header Authorization")

        token = credentials.credentials

        try:
            logger.debug(f"Decoding token for path: {request.url.path}")
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                options={
                    "verify_signature": True,
                    "require": list(REQUIRED_CLAIMS),
                },
            )
            
            # ✅ VALIDAR claims requeridos
            for claim in REQUIRED_CLAIMS:
                if claim not in payload:
                    logger.error(f"Missing required claim: {claim}")
                    raise HTTPException(status_code=400, detail=f"Falta claim requerido: {claim}")
                    
            # ✅ ESTABLECER user en request.state
            request.state.user = {
                "user_id": payload["user_id"],
                "username": payload["username"],
                "email": payload["email"],
                "role": payload["role"],
            }
            
            logger.debug(f"Authenticated user: {request.state.user['username']} (ID: {request.state.user['user_id']})")

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidSignatureError:
            logger.warning("Invalid token signature")
            raise HTTPException(status_code=401, detail="Firma no válida")
        except jwt.MissingRequiredClaimError as e:
            logger.warning(f"Missing required claim: {e.claim}")
            raise HTTPException(status_code=400, detail=f"Falta claim: {e.claim}")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise HTTPException(status_code=401, detail="Token inválido")
        except Exception as e:
            logger.error(f"Unexpected auth error: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Error de autenticación: {str(e)}")

        # ✅ CONTINUAR con la solicitud
        response = await call_next(request)
        return response