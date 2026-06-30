from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.]+$")
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: str | None = Field(default=None, max_length=100)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=500)


class UserBrief(BaseModel):
    """Lightweight user info embedded in posts, comments, stories, reels."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str | None = None
    avatar_url: str | None = None


class UserOut(UserBrief):
    email: EmailStr
    bio: str | None = None
    created_at: datetime


class UserProfile(BaseModel):
    """Public profile shown on the profile page, with aggregate counts."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    created_at: datetime
    post_count: int = 0
    follower_count: int = 0
    following_count: int = 0
    is_following: bool = False
    is_me: bool = False