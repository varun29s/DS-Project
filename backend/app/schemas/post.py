from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserBrief


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    caption: str | None = None
    created_at: datetime
    owner: UserBrief
    like_count: int = 0
    comment_count: int = 0
    liked: bool = False  # whether the current user has liked this post