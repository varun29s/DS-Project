from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud import social
from app.models.post import Post


def create(db: Session, user_id: int, image_url: str, caption: str | None) -> Post:
    post = Post(user_id=user_id, image_url=image_url, caption=caption)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get(db: Session, post_id: int) -> Post | None:
    return db.get(Post, post_id)


def get_user_posts(db: Session, user_id: int, skip: int = 0, limit: int = 30) -> list[Post]:
    return list(
        db.scalars(
            select(Post)
            .where(Post.user_id == user_id)
            .order_by(Post.created_at.desc())
            .offset(skip)
            .limit(limit)
        ).all()
    )


def count_user_posts(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Post).where(Post.user_id == user_id)
    ) or 0


def get_feed(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> list[Post]:
    """Posts from people the user follows, plus their own — newest first."""
    author_ids = social.following_ids(db, user_id) + [user_id]
    return list(
        db.scalars(
            select(Post)
            .where(Post.user_id.in_(author_ids))
            .order_by(Post.created_at.desc())
            .offset(skip)
            .limit(limit)
        ).all()
    )


def delete(db: Session, post: Post) -> None:
    db.delete(post)
    db.commit()


def attach_meta(posts: Iterable[Post], current_user_id: int) -> list[Post]:
    """Set transient like_count / comment_count / liked attributes used by PostOut.

    Relies on the ``likes`` and ``comments`` relationships being loadable.
    """
    result = []
    for post in posts:
        post.like_count = len(post.likes)
        post.comment_count = len(post.comments)
        post.liked = any(like.user_id == current_user_id for like in post.likes)
        result.append(post)
    return result