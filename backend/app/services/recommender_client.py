"""HTTP client for the recommendation microservice.

Returns ``None`` on any network/timeout error so callers can fall back to
the chronological feed gracefully.
"""
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_recommendations(user_id: int, limit: int = 20) -> list[dict] | None:
    """Call the recommender and return a ranked list of ``{"reel_id": int, "reason": str}`` dicts.

    Returns ``None`` if the service is unreachable or returns an error.
    """
    try:
        url = f"{settings.RECOMMENDER_URL}/recommend"
        resp = httpx.get(
            url,
            params={"user_id": user_id, "limit": limit},
            timeout=settings.RECOMMENDER_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Recommender unavailable (%s) — using fallback feed", exc)
        return None
