import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import Task, TaskStatus, TaskPriority, User


@pytest.mark.asyncio
async def test_create_task(authorized_client: AsyncClient, test_user_in_db: User):
    """Test creating a task."""
    task_data = {
        "title": "New Task",
        "description": "This is a new task",
        "status": TaskStatus.TODO.value,
        "priority": TaskPriority.HIGH.value
    }
    
    response = await authorized_client.post("/tasks/", json=task_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert data["status"] == task_data["status"]
    assert data["priority"] == task_data["priority"]
    assert data["user_id"] == test_user_in_db.id
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_task_validation(authorized_client: AsyncClient):
    """Test validation when creating a task with invalid data."""
    # Missing title (required field)
    task_data = {
        "description": "This is a new task",
        "status": TaskStatus.TODO.value,
        "priority": TaskPriority.HIGH.value
    }
    
    response = await authorized_client.post("/tasks/", json=task_data)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "title" in response.json()["detail"]["errors"][0]["loc"]


@pytest.mark.asyncio
async def test_read_tasks(
    authorized_client: AsyncClient,
    test_user_in_db: User,
    test_task_in_db: Task
):
    """Test reading all tasks."""
    response = await authorized_client.get("/tasks/")
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_task_in_db.id
    assert data[0]["title"] == test_task_in_db.title
    assert data[0]["description"] == test_task_in_db.description
    assert data[0]["status"] == test_task_in_db.status.value
    assert data[0]["priority"] == test_task_in_db.priority.value
    assert data[0]["user_id"] == test_user_in_db.id


@pytest.mark.asyncio
async def test_read_tasks_with_filters(
    authorized_client: AsyncClient,
    test_user_in_db: User,
    test_task_in_db: Task
):
    """Test reading tasks with filters."""
    # Create an additional task with different status
    task_data = {
        "title": "New Task",
        "description": "This is a new task",
        "status": TaskStatus.IN_PROGRESS.value,
        "priority": TaskPriority.HIGH.value
    }
    
    await authorized_client.post("/tasks/", json=task_data)
    
    # Filter by status
    response = await authorized_client.get(f"/tasks/?status={TaskStatus.TODO.value}")
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_task_in_db.id
    assert data[0]["status"] == TaskStatus.TODO.value


@pytest.mark.asyncio
async def test_read_task(
    authorized_client: AsyncClient,
    test_task_in_db: Task
):
    """Test reading a single task."""
    response = await authorized_client.get(f"/tasks/{test_task_in_db.id}")
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["id"] == test_task_in_db.id
    assert data["title"] == test_task_in_db.title
    assert data["description"] == test_task_in_db.description
    assert data["status"] == test_task_in_db.status.value
    assert data["priority"] == test_task_in_db.priority.value


@pytest.mark.asyncio
async def test_read_nonexistent_task(authorized_client: AsyncClient):
    """Test reading a task that doesn't exist."""
    response = await authorized_client.get("/tasks/999")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_task(
    authorized_client: AsyncClient,
    test_task_in_db: Task
):
    """Test updating a task."""
    task_update = {
        "title": "Updated Task",
        "status": TaskStatus.IN_PROGRESS.value
    }
    
    response = await authorized_client.patch(
        f"/tasks/{test_task_in_db.id}", json=task_update
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["id"] == test_task_in_db.id
    assert data["title"] == task_update["title"]
    assert data["status"] == task_update["status"]
    assert data["description"] == test_task_in_db.description  # Unchanged
    assert data["priority"] == test_task_in_db.priority.value  # Unchanged


@pytest.mark.asyncio
async def test_update_nonexistent_task(authorized_client: AsyncClient):
    """Test updating a task that doesn't exist."""
    task_update = {"title": "Updated Task"}
    
    response = await authorized_client.patch("/tasks/999", json=task_update)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_task(
    authorized_client: AsyncClient,
    test_task_in_db: Task,
    test_engine
):
    """Test deleting a task."""
    task_id = test_task_in_db.id
    
    response = await authorized_client.delete(f"/tasks/{task_id}")
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify task is deleted from database
    async with AsyncSession(bind=test_engine, expire_on_commit=False) as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        assert task is None


@pytest.mark.asyncio
async def test_delete_nonexistent_task(authorized_client: AsyncClient):
    """Test deleting a task that doesn't exist."""
    response = await authorized_client.delete("/tasks/999")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test accessing endpoints without authentication."""
    # Try to get tasks
    response = await client.get("/tasks/")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Try to create a task
    task_data = {"title": "Unauthorized Task"}
    
    response = await client.post("/tasks/", json=task_data)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_access_other_user_task(
    authorized_client: AsyncClient,
    superuser_client: AsyncClient,
    superuser_in_db: User
):
    """Test accessing another user's task."""
    # Create a task as superuser
    task_data = {
        "title": "Superuser Task",
        "description": "This is a superuser task"
    }
    
    response = await superuser_client.post("/tasks/", json=task_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    task_id = response.json()["id"]
    
    # Try to access superuser's task as regular user
    response = await authorized_client.get(f"/tasks/{task_id}")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Superuser can access any task
    response = await superuser_client.get("/tasks/")
    
    assert response.status_code == status.HTTP_200_OK