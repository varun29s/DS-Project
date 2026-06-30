from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud import social
from app.models.story import Story

STORY_TTL_HOURS = 24


def create(db: Session, user_id: int, media_url: str, media_type: str) -> Story:
    story = Story(
        user_id=user_id,
        media_url=media_url,
        media_type=media_type,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=STORY_TTL_HOURS),
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    return story


def get_active_feed(db: Session, user_id: int) -> list[Story]:
    """Non-expired stories from followed users + self, oldest first per author."""
    author_ids = social.following_ids(db, user_id) + [user_id]
    return list(
        db.scalars(
            select(Story)
            .where(Story.user_id.in_(author_ids), Story.expires_at > func.now())
            .order_by(Story.user_id, Story.created_at.asc())
        ).all()
    )