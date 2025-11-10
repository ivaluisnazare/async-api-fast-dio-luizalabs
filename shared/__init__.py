# shared/database/__init__.py
from .database import engine, metadata, get_db

__all__ = ["engine", "metadata", "get_db"]