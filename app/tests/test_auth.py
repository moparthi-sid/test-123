import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login(client: AsyncClient, test_user_in_db):
    """Test login with valid credentials."""
    login_data = {
        "username": test_user_in_db.username,
        "password": "testpassword"  # from conftest.py
    }
    
    response = await client.post(
        "/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, test_user_in_db):
    """Test login with invalid credentials."""
    # Wrong password
    login_data = {
        "username": test_user_in_db.username,
        "password": "wrongpassword"
    }
    
    response = await client.post(
        "/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Nonexistent user
    login_data = {
        "username": "nonexistentuser",
        "password": "testpassword"
    }
    
    response = await client.post(
        "/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_protected_endpoint_with_token(authorized_client: AsyncClient):
    """Test accessing protected endpoint with valid token."""
    response = await authorized_client.get("/tasks/")
    
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client: AsyncClient):
    """Test accessing protected endpoint without token."""
    response = await client.get("/tasks/")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token(client: AsyncClient):
    """Test accessing protected endpoint with invalid token."""
    client.headers.update({"Authorization": "Bearer invalidtoken"})
    
    response = await client.get("/tasks/")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED