"""Cubre las reglas de negocio de SubscriptionService.subscribe/unsubscribe:
no suscribirse a uno mismo, no duplicar una suscripción, y no suscribirse
a un artista que no existe (validado vía HTTP a artist-service, Fase 3).
Usa dobles de prueba en memoria — no necesita Postgres ni artist-service
real corriendo."""

import pytest

from services.subscription_service import SubscriptionService


class _FakeRepo:
    def __init__(self):
        self.subscriptions = set()  # {(user_id, artist_id)}
        self.added = []

    async def exists(self, user_id, artist_id):
        return (user_id, artist_id) in self.subscriptions

    async def add(self, user_id, artist_id):
        self.subscriptions.add((user_id, artist_id))
        self.added.append((user_id, artist_id))
        return {"user_id": user_id, "artist_id": artist_id}

    async def remove(self, user_id, artist_id):
        self.subscriptions.discard((user_id, artist_id))

    async def get_user_subscriptions(self, user_id):
        return [
            type("Sub", (), {"artist_id": a, "created_at": None})()
            for (u, a) in self.subscriptions
            if u == user_id
        ]

    async def get_user_subscribed_artists(self, user_id):
        return [a for (u, a) in self.subscriptions if u == user_id]


class _FakeArtistClient:
    def __init__(self, known_artist_ids):
        self.known_artist_ids = known_artist_ids

    async def get(self, path):
        artist_id = int(path.rsplit("/", 1)[-1])
        if artist_id not in self.known_artist_ids:
            return None
        return {"data": {"id": artist_id, "artist_name": f"Artista {artist_id}"}}


def make_service(known_artist_ids=(5,)):
    service = SubscriptionService(_FakeRepo())
    service.artist_client = _FakeArtistClient(set(known_artist_ids))
    return service


async def test_subscribe_success():
    service = make_service(known_artist_ids=(5,))

    await service.subscribe(user_id=1, artist_id=5)

    assert await service.repository.exists(user_id=1, artist_id=5) is True


async def test_subscribe_to_self_raises():
    service = make_service(known_artist_ids=(1,))

    with pytest.raises(ValueError, match="ti mismo"):
        await service.subscribe(user_id=1, artist_id=1)


async def test_subscribe_duplicate_raises():
    service = make_service(known_artist_ids=(5,))
    await service.subscribe(user_id=1, artist_id=5)

    with pytest.raises(ValueError, match="Ya estás suscrito"):
        await service.subscribe(user_id=1, artist_id=5)


async def test_subscribe_nonexistent_artist_raises():
    service = make_service(known_artist_ids=())  # ningún artista existe

    with pytest.raises(ValueError, match="no existe"):
        await service.subscribe(user_id=1, artist_id=999)


async def test_unsubscribe_nonexistent_raises():
    service = make_service()

    with pytest.raises(ValueError, match="No existe suscripción"):
        await service.unsubscribe(user_id=1, artist_id=5)


async def test_unsubscribe_success():
    service = make_service(known_artist_ids=(5,))
    await service.subscribe(user_id=1, artist_id=5)

    await service.unsubscribe(user_id=1, artist_id=5)

    assert await service.repository.exists(user_id=1, artist_id=5) is False
