from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from handlers.search_handler import router as search_router
from middleware.auth_middleware import AuthMiddleware
from config import settings
import uvicorn

app = FastAPI(title="Search Service", version="0.1")

# debug: Verificar orígenes permitidos
print("Allowed origins:", settings.frontend_origins)

#configuración de CORS - DEBE IR PRIMERO
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware global
app.add_middleware(AuthMiddleware)

# Router de búsqueda
app.include_router(search_router, prefix="/search", tags=["Search"])


# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)
