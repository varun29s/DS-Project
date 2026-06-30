from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_by_login(db: Session, login: str) -> User | None:
    """Look up a user by either username or email (used at login)."""
    return db.scalar(select(User).where((User.username == login) | (User.email == login)))


def create(db: Session, user_in: UserCreate) -> User:
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update(db: Session, user: User, updates: UserUpdate) -> User:
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def set_avatar(db: Session, user: User, avatar_url: str) -> User:
    user.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return user