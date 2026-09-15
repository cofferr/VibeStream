from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status
from services.subscription_service import SubscriptionService
from database.connection import get_db
from repositories.repository import SQLAlchemySubscriptionRepository

router = APIRouter(prefix="", tags=["subscriptions"])


# 🔹 Factory para inyectar el servicio
async def get_subscription_service(session=Depends(get_db)) -> SubscriptionService:
    repo = SQLAlchemySubscriptionRepository(session)
    return SubscriptionService(repo)


@router.post("/subscribe/{artist_id}", status_code=status.HTTP_201_CREATED)
async def subscribe(
    artist_id: int,
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
):
    user_id = request.state.user["user_id"]
    try:
        subscription = await service.subscribe(user_id=user_id, artist_id=artist_id)
        return {
            "message": "Suscripción exitosa",
            "artist_id": subscription.artist_id,
            "user_id": subscription.user_id,
            "created_at": subscription.created_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/unsubscribe/{artist_id}", status_code=status.HTTP_200_OK)
async def unsubscribe(
    artist_id: int,
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
):
    user_id = request.state.user["user_id"]
    try:
        await service.unsubscribe(user_id=user_id, artist_id=artist_id)
        return {
            "message": "Desuscripción exitosa",
            "artist_id": artist_id,
            "user_id": user_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# 🔹 Endpoint existente: verificar si estoy suscrito
@router.get("/status/{artist_id}", status_code=status.HTTP_200_OK)
async def check_subscription(
    artist_id: int,
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
):
    user_id = request.state.user["user_id"]
    is_subscribed = await service.repository.exists(
        user_id=user_id, artist_id=artist_id
    )
    return {
        "artist_id": artist_id,
        "user_id": user_id,
        "is_subscribed": is_subscribed,
    }


# 🔹 NUEVOS ENDPOINTS


@router.get("/my-subscriptions", status_code=status.HTTP_200_OK)
async def get_my_subscriptions(
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Obtiene todas las suscripciones del usuario con información completa"""
    user_id = request.state.user["user_id"]

    subscriptions = await service.get_user_subscriptions_enriched(user_id)

    return {
        "user_id": user_id,
        "total_subscriptions": len(subscriptions),
        "subscriptions": subscriptions,
    }


@router.get("/my-artists", status_code=status.HTTP_200_OK)
async def get_my_subscribed_artists(
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Obtiene solo los IDs de los artistas a los que está suscrito el usuario"""
    user_id = request.state.user["user_id"]

    artist_ids = await service.get_user_subscribed_artists(user_id)

    return {
        "user_id": user_id,
        "total_artists": len(artist_ids),
        "artist_ids": artist_ids,
    }


@router.get("/subscription-count", status_code=status.HTTP_200_OK)
async def get_subscription_count(
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Obtiene el número total de suscripciones del usuario"""
    user_id = request.state.user["user_id"]

    count = await service.get_subscription_count(user_id)

    return {"user_id": user_id, "subscription_count": count}
