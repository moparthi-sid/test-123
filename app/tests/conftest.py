import asyncio
from typing import AsyncGenerator, Dict, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.auth.utils import create_access_token, get_password_hash
from app.database import get_session
from app.main import app as main_app
from app.models import User, Task, TaskStatus, TaskPriority

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for testing
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)


async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    session = AsyncSession(bind=test_engine, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()


# Override the get_session dependency
@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI app with overridden dependencies."""
    main_app.dependency_overrides[get_session] = get_test_session
    return main_app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Set up the test database before each test."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Run test
    yield
    
    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def test_user() -> Dict[str, str]:
    """Create a test user for authentication."""
    return {
        "username": "testuser",
        "password": "testpassword",
        "email": "test@example.com",
        "full_name": "Test User"
    }


@pytest_asyncio.fixture
async def superuser() -> Dict[str, str]:
    """Create a test superuser for authentication."""
    return {
        "username": "admin",
        "password": "adminpassword",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "is_superuser": True
    }


@pytest_asyncio.fixture
async def test_user_in_db(test_user: Dict[str, str]) -> AsyncGenerator[User, None]:
    """Create a test user in the database."""
    async with AsyncSession(bind=test_engine, expire_on_commit=False) as session:
        db_user = User(
            username=test_user["username"],
            email=test_user["email"],
            full_name=test_user["full_name"],
            hashed_password=get_password_hash(test_user["password"]),
            is_active=True,
            is_superuser=False
        )
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        yield db_user


@pytest_asyncio.fixture
async def superuser_in_db(superuser: Dict[str, str]) -> AsyncGenerator[User, None]:
    """Create a test superuser in the database."""
    async with AsyncSession(bind=test_engine, expire_on_commit=False) as session:
        db_user = User(
            username=superuser["username"],
            email=superuser["email"],
            full_name=superuser["full_name"],
            hashed_password=get_password_hash(superuser["password"]),
            is_active=True,
            is_superuser=True
        )
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        yield db_user


@pytest_asyncio.fixture
async def token(test_user_in_db: User) -> str:
    """Create a token for the test user."""
    return create_access_token(data={"sub": test_user_in_db.username})


@pytest_asyncio.fixture
async def superuser_token(superuser_in_db: User) -> str:
    """Create a token for the superuser."""
    return create_access_token(data={"sub": superuser_in_db.username})


@pytest_asyncio.fixture
async def authorized_client(client: AsyncClient, token: str) -> AsyncClient:
    """Create an authenticated client."""
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest_asyncio.fixture
async def superuser_client(client: AsyncClient, superuser_token: str) -> AsyncClient:
    """Create an authenticated superuser client."""
    client.headers.update({"Authorization": f"Bearer {superuser_token}"})
    return client


@pytest_asyncio.fixture
async def test_task(test_user_in_db: User) -> Dict:
    """Create a test task."""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "status": TaskStatus.TODO.value,
        "priority": TaskPriority.MEDIUM.value,
        "user_id": test_user_in_db.id
    }


@pytest_asyncio.fixture
async def test_task_in_db(test_user_in_db: User, test_task: Dict) -> AsyncGenerator[Task, None]:
    """Create a test task in the database."""
    async with AsyncSession(bind=test_engine, expire_on_commit=False) as session:
        db_task = Task(
            title=test_task["title"],
            description=test_task["description"],
            status=test_task["status"],
            priority=test_task["priority"],
            user_id=test_user_in_db.id
        )
        session.add(db_task)
        await session.commit()
        await session.refresh(db_task)
        yield db_task