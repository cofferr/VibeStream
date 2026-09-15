# content-service/middleware/auth_middleware.py
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
        # ✅ PERMITIR SOLICITUDES OPTIONS (CORS PREFLIGHT) SIN AUTENTICACIÓN
        if request.method == "OPTIONS":
            return await call_next(request)
            
        # ✅ EXCLUIR RUTAS QUE NO REQUIERAN AUTENTICACIÓN
        if request.url.path.startswith("/health") or request.url.path.startswith("/files"):
            return await call_next(request)

        print(f"🔍 [Content] Headers recibidos: {dict(request.headers)}")
        
        try:
            auth = HTTPBearer(auto_error=False)
            credentials = await auth(request)
            
            print(f"🔍 [Content] Credentials: {credentials}")
            
            if credentials is None:
                print("❌ [Content] No se encontró header Authorization")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Falta header Authorization"},
                    headers={
                        "Access-Control-Allow-Origin": "http://localhost:5173",
                        "Access-Control-Allow-Credentials": "true",
                    }
                )

            token = credentials.credentials
            print(f"🔍 [Content] Token recibido: {token}")

            # Verificar expiración manualmente primero
            try:
                decoded_without_verify = jwt.decode(token, options={"verify_signature": False})
                print(f"🔍 [Content] Token decodificado (sin verificar): {decoded_without_verify}")
                
                # Verificar expiración
                exp = decoded_without_verify.get('exp')
                if exp and exp < time.time():
                    print(f"❌ [Content] Token expirado. Exp: {exp}, Now: {time.time()}")
                    raise jwt.ExpiredSignatureError("Token expirado")
                    
            except Exception as e:
                print(f"❌ [Content] Error en decodificación básica: {e}")
                raise

            # Ahora verificar con el secret
            print(f"🔍 [Content] Verificando con secret: {settings.jwt_secret[:10]}...")
            print(f"🔍 [Content] Algorithm: {settings.jwt_algorithm}")
            
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                options={
                    "verify_signature": True,
                    "require": list(REQUIRED_CLAIMS),
                },
            )
            
            print(f"✅ [Content] Token válido. Payload: {payload}")

            request.state.user = {
                "user_id": payload["user_id"],
                "username": payload["username"],
                "email": payload["email"],
                "role": payload["role"],
            }

            return await call_next(request)
            
        except jwt.ExpiredSignatureError as e:
            print(f"❌ [Content] Token expirado: {e}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Token expirado"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        except jwt.InvalidSignatureError as e:
            print(f"❌ [Content] Firma no válida: {e}")
            print(f"❌ [Content] ¿El JWT_SECRET coincide con el del servicio de auth?")
            return JSONResponse(
                status_code=401,
                content={"detail": "Firma no válida"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        except jwt.MissingRequiredClaimError as e:
            print(f"❌ [Content] Falta claim requerido: {e}")
            print(f"❌ [Content] Claims requeridos: {REQUIRED_CLAIMS}")
            return JSONResponse(
                status_code=400,
                content={"detail": f"Falta claim: {e.claim}"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173", 
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        except jwt.InvalidTokenError as e:
            print(f"❌ [Content] Token inválido: {e}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Token inválido"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        except Exception as e:
            print(f"❌ [Content] Error inesperado en auth: {e}")
            import traceback
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={"detail": "Error en autenticación"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )