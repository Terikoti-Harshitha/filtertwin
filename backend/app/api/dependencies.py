"""
API Dependencies for FastAPI routes.
"""

from app.database.session import get_db

__all__ = ["get_db"]
