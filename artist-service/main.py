from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from handlers.artist_handler import router as artist_router
from middleware.auth_middleware import AuthMiddleware
from config import settings
import uvicorn
import traceback

app = FastAPI(title="Artist Service", version="0.1")

# Servir archivos de directorio de almacenamiento

# Debug: Verificar los orígenes permitidos
print("Allowed origins:", settings.frontend_origins)

# Configuración de CORS - DEBE IR PRIMERO
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar middleware de autenticación
app.add_middleware(AuthMiddleware)

# Rutas
app.include_router(artist_router, prefix="/artists", tags=["artists"])


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Manejo global de excepciones para asegurar headers CORS
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = str(exc)
    print(f"Global error handler: {error_detail}")
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Credentials": "true",
        },
    )


# Permitir ejecución directa con python3 main.py
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)

