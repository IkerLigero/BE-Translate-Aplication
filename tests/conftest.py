import pytest
import asyncio
import os
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import get_async_db
from app.api.deps import get_current_user
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# 1. Configuation for Windows compatibility with asyncio event loop
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost/tms_db"


# 2. Force the use of a single event loop for all tests to avoid "RuntimeError: This event loop is already running"
# Fixure for the event loop
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Fixure for the database engine and session
@pytest.fixture(scope="session")
async def engine():
    # NullPool prevents background connections from breaking the event loop
    engine = create_async_engine(
        DATABASE_URL, 
        poolclass=NullPool,
        echo=False
    )
    yield engine
    await engine.dispose()


# Fixture for a database session with automatic rollback after each test
@pytest.fixture
async def db_session(engine):
    """Fixture for a database session with automatic rollback."""
    async with engine.connect() as connection:
        transaction = await connection.begin()
        # Force the session to use the connection that already has the correct event loop
        session = AsyncSession(bind=connection, expire_on_commit=False)
        
        yield session
        
        await session.close()
        await transaction.rollback() # Rollback after each test to maintain isolation


# Fixture for the HTTP client with dependency overrides
@pytest.fixture
async def client(db_session):
    """HTTP client with overrides."""
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_async_db] = _get_test_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# Mock user and authentication override for testing
@pytest.fixture
def mock_user():
    return type("FakeUser", (), {"id": 1, "email": "test@example.com", "is_active": True})()


# Fixture to override authentication and provide a mock user
@pytest.fixture
def auth_override(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield mock_user
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]