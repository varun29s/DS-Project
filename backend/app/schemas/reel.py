from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserBrief


class ReelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_url: str
    thumbnail_url: str | None = None
    caption: str | None = None
    created_at: datetime
    owner: UserBrief
    like_count: int = 0
    view_count: int = 0
    liked: bool = False
    # Populated by the recommender (e.g. "Popular right now", "Based on #travel").
    reason: str | None = None