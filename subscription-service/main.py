from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from handlers.subscription_handler import router as subscription_router
from middleware.auth_middleware import AuthMiddleware
from config import settings
import uvicorn

app = FastAPI(title="Subscription Service", version="0.1")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware global
app.add_middleware(AuthMiddleware)

# Router de suscripciones
app.include_router(subscription_router, prefix="/subscriptions", tags=["Subscriptions"])


# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    # Usar el puerto configurado en settings para respetar la variable de entorno
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)
