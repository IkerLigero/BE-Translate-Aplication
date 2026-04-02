from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os

# 1. URLs (Necesitamos una para cada driver)
# El driver asyncpg es para FastAPI, el driver psycogp2 (por defecto) es para Celery/Sync
ASYNC_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/tms_db")
SYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# 2. Configuración ASÍNCRONA (Para tus nuevos endpoints y Locust)
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 3. Configuración SÍNCRONA (Para el Worker/Celery y el endpoint de prueba sync)
sync_engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base = declarative_base()

# 4. Dependencias para FastAPI
# Esta es la que usará tu endpoint ASYNC
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

# Esta es la que usará tu endpoint SYNC (la antigua)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()