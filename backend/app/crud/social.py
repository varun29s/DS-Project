from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.social import Comment, Follow, Like


# --- Follows ---
def is_following(db: Session, follower_id: int, following_id: int) -> bool:
    return db.get(Follow, (follower_id, following_id)) is not None


def follow(db: Session, follower_id: int, following_id: int) -> None:
    if follower_id == following_id:
        return
    if not is_following(db, follower_id, following_id):
        db.add(Follow(follower_id=follower_id, following_id=following_id))
        db.commit()


def unfollow(db: Session, follower_id: int, following_id: int) -> None:
    db.execute(
        delete(Follow).where(
            Follow.follower_id == follower_id, Follow.following_id == following_id
        )
    )
    db.commit()


def follower_count(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Follow).where(Follow.following_id == user_id)
    ) or 0


def following_count(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Follow).where(Follow.follower_id == user_id)
    ) or 0


def following_ids(db: Session, user_id: int) -> list[int]:
    return list(
        db.scalars(select(Follow.following_id).where(Follow.follower_id == user_id)).all()
    )


def get_followers(db: Session, user_id: int) -> list:
    """Return the list of User objects who follow this user."""
    from app.models.user import User

    return list(
        db.scalars(
            select(User)
            .join(Follow, Follow.follower_id == User.id)
            .where(Follow.following_id == user_id)
            .order_by(Follow.created_at.desc())
        ).all()
    )


def get_following(db: Session, user_id: int) -> list:
    """Return the list of User objects this user follows."""
    from app.models.user import User

    return list(
        db.scalars(
            select(User)
            .join(Follow, Follow.following_id == User.id)
            .where(Follow.follower_id == user_id)
            .order_by(Follow.created_at.desc())
        ).all()
    )


# --- Likes ---
def like_post(db: Session, user_id: int, post_id: int) -> None:
    exists = db.scalar(
        select(Like).where(Like.user_id == user_id, Like.post_id == post_id)
    )
    if not exists:
        db.add(Like(user_id=user_id, post_id=post_id))
        db.commit()


def unlike_post(db: Session, user_id: int, post_id: int) -> None:
    db.execute(delete(Like).where(Like.user_id == user_id, Like.post_id == post_id))
    db.commit()


# --- Comments ---
def add_comment(db: Session, user_id: int, post_id: int, text: str) -> Comment:
    comment = Comment(user_id=user_id, post_id=post_id, text=text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comments(db: Session, post_id: int, skip: int = 0, limit: int = 50) -> list[Comment]:
    return list(
        db.scalars(
            select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at.asc())
            .offset(skip)
            .limit(limit)
        ).all()
    )