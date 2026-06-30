from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserBrief


class StoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    media_url: str
    media_type: str
    created_at: datetime
    expires_at: datetime
    owner: UserBrief


class StoryTray(BaseModel):
    """Active stories grouped by author — what the home page story tray renders."""

    user: UserBrief
    stories: list[StoryOut]