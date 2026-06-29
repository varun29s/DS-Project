from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Reel(Base):
    """A short video reel — shown in the home reels feed."""

    __tablename__ = "reels"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    video_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    caption: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    owner: Mapped["User"] = relationship(back_populates="reels")
    likes: Mapped[list["ReelLike"]] = relationship(
        back_populates="reel", cascade="all, delete-orphan"
    )
    views: Mapped[list["ReelView"]] = relationship(
        back_populates="reel", cascade="all, delete-orphan"
    )