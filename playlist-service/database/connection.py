from config import settings
from vibestream_common.db import Base, make_engine_and_session, make_get_db

engine, AsyncSessionLocal = make_engine_and_session(
    settings.db_url,
    pool_size=10,
    max_overflow=20,
)
get_db = make_get_db(AsyncSessionLocal)

__all__ = ["Base", "engine", "AsyncSessionLocal", "get_db"]
