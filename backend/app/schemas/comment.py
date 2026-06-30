from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserBrief


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2200)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    created_at: datetime
    owner: UserBrief