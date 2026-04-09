import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 1. URL for async database operations using the asyncpg driver.
ASYNC_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/tms_db")

# 2. ASYNC CONFIGURATION
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)

# The async_sessionmaker produces new AsyncSession objects when called.
# expire_on_commit=False prevents SQLAlchemy from trying to refresh objects 
# after a commit, which is the standard practice in async flows.
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 3. BASE CLASS
# Used by your models (Translation, etc.) to inherit from SQLAlchemy's declarative system.
Base = declarative_base()

# 4. Dependency for FastAPI
# This will be injected into your endpoints via Depends(get_async_db).
# The 'async with' block ensures the session is automatically closed after the request.
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session