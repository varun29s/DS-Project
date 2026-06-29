"""Imports Base together with every model so that ``Base.metadata`` knows about
all tables (used by ``create_all`` and, later, Alembic autogenerate)."""
from app.db.base_class import Base  # noqa: F401

# Import models for their side effect of registering with Base.metadata.
from app.models.user import User  # noqa: F401
from app.models.post import Post  # noqa: F401
from app.models.story import Story  # noqa: F401
from app.models.reel import Reel  # noqa: F401
from app.models.social import Follow, Like, Comment, ReelLike, ReelView  # noqa: F401