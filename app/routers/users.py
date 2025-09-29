from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth.utils import get_password_hash, get_current_active_user
from app.database import get_session
from app.models import User, UserCreate, UserRead, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate, session: AsyncSession = Depends(get_session)
):
    """Create a new user"""
    # Check if user with email already exists
    query = select(User).where(User.email == user.email)
    result = await session.execute(query)
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username is taken
    query = select(User).where(User.username == user.username)
    result = await session.execute(query)
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
    )
    
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    
    return db_user


@router.get("/", response_model=List[UserRead])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get all users"""
    query = select(User).offset(skip).limit(limit)
    result = await session.execute(query)
    users = result.scalars().all()
    return users


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific user by ID"""
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"User with ID {user_id} not found"
        )
    
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    # Check if user is updating their own profile or is a superuser
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    """Update a user partially"""
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    db_user = result.scalars().first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"User with ID {user_id} not found"
        )
    
    # Check email uniqueness if being updated
    if user_update.email and user_update.email != db_user.email:
        query = select(User).where(User.email == user_update.email)
        result = await session.execute(query)
        existing_user = result.scalars().first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check username uniqueness if being updated
    if user_update.username and user_update.username != db_user.username:
        query = select(User).where(User.username == user_update.username)
        result = await session.execute(query)
        existing_user = result.scalars().first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Update password if provided
    user_data = user_update.dict(exclude_unset=True)
    if "password" in user_data:
        # Hash the password
        hashed_password = get_password_hash(user_data.pop("password"))
        user_data["hashed_password"] = hashed_password
    
    # Update user attributes that are provided
    for key, value in user_data.items():
        setattr(db_user, key, value)
    
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    # Only superusers can delete users
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    """Delete a user"""
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"User with ID {user_id} not found"
        )
    
    await session.delete(user)
    await session.commit()
    
    return None