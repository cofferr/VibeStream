"""Cubre la lista de excepciones públicas del AuthMiddleware de
artist-service: qué rutas quedan sin JWT es una decisión de seguridad
real (GET /artists/{id} es pública a propósito porque otros servicios
internos la consumen sin token de usuario, Fase 3), no un detalle de
implementación — vale la pena un test explícito en vez de confiar en
revisarlo a mano cada vez que cambia una ruta."""

import time

import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient

from config import settings
from middleware.auth_middleware import AuthMiddleware


def _make_app() -> TestClient:
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # registrada antes de /{artist_id}, igual que en artist_handler.py,
    # para que FastAPI no la matchee como artist_id="by-user"
    @app.get("/artists/by-user/{user_id}")
    def get_artist_by_user(user_id: str):
        return {"user_id": user_id}

    @app.get("/artists/{artist_id}")
    def get_artist(artist_id: str):
        return {"artist_id": artist_id}

    @app.post("/artists/{artist_id}")
    def weird_post(artist_id: str):
        return {"ok": True}

    @app.get("/artists/me")
    def get_me():
        return {"me": True}

    return TestClient(app)


def _valid_token() -> str:
    payload = {
        "user_id": 1,
        "username": "juan",
        "email": "juan@example.com",
        "role": "user",
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def test_health_is_public():
    client = _make_app()
    resp = client.get("/health")
    assert resp.status_code == 200


def test_get_artist_by_id_is_public():
    client = _make_app()
    resp = client.get("/artists/123")
    assert resp.status_code == 200


def test_get_artist_by_user_id_is_public():
    """Fase 6: content-service la usa para resolver el artist_id del
    usuario autenticado, sin JWT de usuario para reenviar."""
    client = _make_app()
    resp = client.get("/artists/by-user/1")
    assert resp.status_code == 200


def test_get_artist_me_requires_auth():
    """"/me" no debe matchear el patrón numérico de la excepción pública."""
    client = _make_app()
    resp = client.get("/artists/me")
    assert resp.status_code == 401


def test_post_to_artist_id_requires_auth():
    """La excepción pública es solo para GET — un POST al mismo path debe
    seguir exigiendo autenticación."""
    client = _make_app()
    resp = client.post("/artists/123")
    assert resp.status_code == 401


def test_valid_token_is_accepted():
    client = _make_app()
    resp = client.get("/artists/me", headers={"Authorization": f"Bearer {_valid_token()}"})
    assert resp.status_code == 200


def test_missing_token_returns_401_not_500():
    """Regresión del bug real de esta sesión: el middleware compartido
    lanzaba HTTPException dentro de dispatch(), que Starlette intercepta
    como 500 genérico en vez del 401 real."""
    client = _make_app()
    resp = client.get("/artists/me")
    assert resp.status_code == 401
    assert resp.json()["detail"] != "Internal server error"
