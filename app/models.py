from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import EmailStr, Field
from sqlmodel import Field, Relationship, SQLModel


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskBase(SQLModel):
    title: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    status: TaskStatus = Field(default=TaskStatus.TODO)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: Optional[datetime] = Field(default=None)


class Task(TaskBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    # Relationship
    user: Optional["User"] = Relationship(back_populates="tasks")


class TaskCreate(TaskBase):
    pass


class TaskRead(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: Optional[int] = None


class TaskUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None


class UserBase(SQLModel):
    email: EmailStr = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    full_name: Optional[str] = None


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    tasks: List["Task"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime


class UserUpdate(SQLModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None