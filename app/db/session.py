from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os

# 1. URL that SQLAlchemy will use to connect to the database. We have two: one for async and one for sync operations.
# The asyncpg driver is for FastAPI, the psycopg2 driver (default) is for Celery/Sync
ASYNC_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/tms_db")
SYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# 2. ASYNC CONFIGURATION (For your new endpoints and Locust)
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 3. SYNC CONFIGURATION (For the Worker/Celery and the sync test endpoint)
sync_engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base = declarative_base()

# 4. Dependencies for FastAPI
# This is the one your ASYNC endpoint will use (the new one for Locust)
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

# This is the one your SYNC endpoint will use (the old one for Celery and the sync test)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()