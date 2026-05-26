"""FastAPI dependency injection — DB session, cache, fetcher router."""

from core.database import SessionLocal
from core.cache.manager import get_cache
from core.fetchers.router import get_router


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
