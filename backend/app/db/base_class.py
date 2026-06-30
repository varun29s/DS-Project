"""Declarative base class for all ORM models."""
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass