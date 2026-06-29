"""Minimal read-only ORM models mirroring the backend tables the recommender needs.

Only the columns used for ranking are mapped; the service never writes or creates
these tables.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Reel(Base):
    __tablename__ = "reels"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    caption: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ReelLike(Base):
    __tablename__ = "reel_likes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reel_id: Mapped[int] = mapped_column(ForeignKey("reels.id"))


class ReelView(Base):
    __tablename__ = "reel_views"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reel_id: Mapped[int] = mapped_column(ForeignKey("reels.id"))
    count: Mapped[int] = mapped_column()


class Follow(Base):
    __tablename__ = "follows"

    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    following_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
