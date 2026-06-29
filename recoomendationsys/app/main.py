"""Reel recommendation microservice (the "ML" service).

Reads the shared database, ranks reels per user, and returns ranked reel IDs +
reasons. The main backend calls this and hydrates the IDs into full reel objects.

Run from the ``recommendsys/`` directory:
    uvicorn app.main:app --reload --port 8001
"""
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app import recommender
from app.config import settings
from app.db import get_db
from app.schemas import RecommendationResponse

app = FastAPI(title=settings.SERVICE_NAME)


@app.get("/", tags=["health"])
def root() -> dict:
    return {"status": "ok", "service": settings.SERVICE_NAME}


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "healthy"}


@app.get("/recommend/reels", response_model=RecommendationResponse, tags=["recommend"])
def recommend_reels(
    user_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    items = recommender.recommend(db, user_id, limit=limit)
    return RecommendationResponse(user_id=user_id, count=len(items), items=items)
