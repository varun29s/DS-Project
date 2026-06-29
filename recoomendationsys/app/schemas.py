from pydantic import BaseModel


class RecommendationItem(BaseModel):
    reel_id: int
    score: float
    reason: str


class RecommendationResponse(BaseModel):
    user_id: int
    count: int
    items: list[RecommendationItem]
