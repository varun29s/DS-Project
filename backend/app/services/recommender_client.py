"""Client for the recommendation (ML) microservice.

Keeps the backend decoupled from the ranking engine: it asks the service for
ranked reel IDs and reasons, and hydrates them into ORM objects elsewhere. If the
service is unreachable, returns ``None`` so callers can fall back gracefully.
"""
import httpx

from app.core.config import settings


def get_recommendations(user_id: int, limit: int = 20) -> list[dict] | None:
    """Return ``[{reel_id, score, reason}]`` or ``None`` if the ML service is down."""
    try:
        resp = httpx.get(
            f"{settings.RECOMMENDER_URL}/recommend/reels",
            params={"user_id": user_id, "limit": limit},
            timeout=settings.RECOMMENDER_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("items", [])
    except (httpx.HTTPError, ValueError):
        return None