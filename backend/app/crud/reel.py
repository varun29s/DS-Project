from collections.abc import Iterable

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.reels import Reel
from app.models.social import ReelLike, ReelView


def create(
    db: Session,
    user_id: int,
    video_url: str,
    thumbnail_url: str | None,
    caption: str | None,
) -> Reel:
    reel = Reel(
        user_id=user_id,
        video_url=video_url,
        thumbnail_url=thumbnail_url,
        caption=caption,
    )
    db.add(reel)
    db.commit()
    db.refresh(reel)
    return reel


def get(db: Session, reel_id: int) -> Reel | None:
    return db.get(Reel, reel_id)


def get_by_ids(db: Session, ids: list[int]) -> list[Reel]:
    """Fetch reels by id (unordered) — caller restores the requested order."""
    if not ids:
        return []
    return list(db.scalars(select(Reel).where(Reel.id.in_(ids))).all())


def get_feed(db: Session, skip: int = 0, limit: int = 20) -> list[Reel]:
    """Plain chronological feed (newest first) — used by Explore and as a fallback."""
    return list(
        db.scalars(
            select(Reel).order_by(Reel.created_at.desc()).offset(skip).limit(limit)
        ).all()
    )


def get_user_reels(db: Session, user_id: int, skip: int = 0, limit: int = 30) -> list[Reel]:
    return list(
        db.scalars(
            select(Reel)
            .where(Reel.user_id == user_id)
            .order_by(Reel.created_at.desc())
            .offset(skip)
            .limit(limit)
        ).all()
    )


# --- Interactions (recommendation signals) ---
def like(db: Session, user_id: int, reel_id: int) -> None:
    exists = db.scalar(
        select(ReelLike).where(ReelLike.user_id == user_id, ReelLike.reel_id == reel_id)
    )
    if not exists:
        db.add(ReelLike(user_id=user_id, reel_id=reel_id))
        db.commit()


def unlike(db: Session, user_id: int, reel_id: int) -> None:
    db.execute(
        delete(ReelLike).where(ReelLike.user_id == user_id, ReelLike.reel_id == reel_id)
    )
    db.commit()


def record_view(db: Session, user_id: int, reel_id: int, watch_ms: int = 0) -> None:
    row = db.scalar(
        select(ReelView).where(ReelView.user_id == user_id, ReelView.reel_id == reel_id)
    )
    if row:
        row.count += 1
        row.watch_ms += int(watch_ms or 0)
    else:
        row = ReelView(
            user_id=user_id, reel_id=reel_id, count=1, watch_ms=int(watch_ms or 0)
        )
        db.add(row)
    db.commit()


def attach_counts(db: Session, reels: Iterable[Reel], user_id: int) -> list[Reel]:
    """Set transient like_count / view_count / liked / reason attributes for ReelOut."""
    reels = list(reels)
    ids = [r.id for r in reels]
    if not ids:
        return reels

    like_counts = {
        rid: c
        for rid, c in db.execute(
            select(ReelLike.reel_id, func.count())
            .where(ReelLike.reel_id.in_(ids))
            .group_by(ReelLike.reel_id)
        )
    }
    view_counts = {
        rid: int(s)
        for rid, s in db.execute(
            select(ReelView.reel_id, func.coalesce(func.sum(ReelView.count), 0))
            .where(ReelView.reel_id.in_(ids))
            .group_by(ReelView.reel_id)
        )
    }
    liked = set(
        db.scalars(
            select(ReelLike.reel_id).where(
                ReelLike.user_id == user_id, ReelLike.reel_id.in_(ids)
            )
        ).all()
    )

    for r in reels:
        r.like_count = like_counts.get(r.id, 0)
        r.view_count = view_counts.get(r.id, 0)
        r.liked = r.id in liked
        if not hasattr(r, "reason"):
            r.reason = None
    return reels    