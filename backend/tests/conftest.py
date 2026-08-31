"""
FinPilot — Pytest Test Configuration & Fixtures
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.base import Base
from app.db.session import get_db
from app.api.v1.admin import seed_database

# Use in-memory SQLite for fast isolated testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# The default user ID that seed_database creates when no user is passed
TEST_USER_ID = "00000000-0000-4000-a000-000000000001"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create test tables and seed data for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        # seed_database without a user creates a User with TEST_USER_ID
        await seed_database(session)
        await session.commit()
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Test client overriding the get_db dependency."""
    async def override_get_db():
        yield db_session

    # Return a User whose id matches the seeded data
    test_user = User(
        id=TEST_USER_ID,
        email="alex.morgan@finpilot.ai",
        name="Alex Morgan",
    )
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: test_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()
