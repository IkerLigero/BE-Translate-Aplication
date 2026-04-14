import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# 1. DATABASE URLs
ASYNC_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/tms_db")
# Convert async URL to sync for Celery (removes +asyncpg)
SYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# 2. ASYNC CONFIGURATION (For FastAPI & Locust)
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 3. SYNC CONFIGURATION (For Celery/Worker)
# This is what app.worker.tasks.py is looking for!
sync_engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base = declarative_base()

# 4. DEPENDENCIES
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

# Sync dependency (if needed)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()