"""Create database tables on startup.

For a small project this is enough. For schema migrations later, swap this for
Alembic (the models are already structured to support autogenerate).
"""
from app.db.base import Base  # noqa: F401  (registers all models on Base.metadata)
from app.db.session import engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)