from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import Task, TaskCreate, TaskRead, TaskUpdate

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate, session: AsyncSession = Depends(get_session)
):
    """Create a new task"""
    db_task = Task.from_orm(task)
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)
    return db_task


@router.get("/", response_model=List[TaskRead])
async def read_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="Filter tasks by status"),
    priority: Optional[str] = Query(None, description="Filter tasks by priority"),
    session: AsyncSession = Depends(get_session),
):
    """Get all tasks with optional filtering"""
    query = select(Task)
    
    # Add filters if provided
    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)
    
    # Add pagination
    query = query.offset(skip).limit(limit)
    
    result = await session.execute(query)
    tasks = result.scalars().all()
    return tasks


@router.get("/{task_id}", response_model=TaskRead)
async def read_task(task_id: int, session: AsyncSession = Depends(get_session)):
    """Get a specific task by ID"""
    query = select(Task).where(Task.id == task_id)
    result = await session.execute(query)
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Task with ID {task_id} not found"
        )
    
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a task partially"""
    query = select(Task).where(Task.id == task_id)
    result = await session.execute(query)
    db_task = result.scalars().first()
    
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Task with ID {task_id} not found"
        )
    
    # Update task attributes that are provided
    task_data = task_update.dict(exclude_unset=True)
    for key, value in task_data.items():
        setattr(db_task, key, value)
    
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)
    
    return db_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, session: AsyncSession = Depends(get_session)):
    """Delete a task"""
    query = select(Task).where(Task.id == task_id)
    result = await session.execute(query)
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Task with ID {task_id} not found"
        )
    
    await session.delete(task)
    await session.commit()
    
    return None