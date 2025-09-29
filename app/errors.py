from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models import TaskStatus, TaskPriority


class TaskNotFoundError(Exception):
    """Raised when a task is not found"""
    def __init__(self, task_id: int):
        self.task_id = task_id
        self.message = f"Task with ID {task_id} not found"
        super().__init__(self.message)


class UserNotFoundError(Exception):
    """Raised when a user is not found"""
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.message = f"User with ID {user_id} not found"
        super().__init__(self.message)


class InvalidTaskStatusError(Exception):
    """Raised when an invalid task status is provided"""
    def __init__(self, status: str):
        self.status = status
        valid_statuses = [s.value for s in TaskStatus]
        self.message = f"Invalid task status: {status}. Valid statuses are: {', '.join(valid_statuses)}"
        super().__init__(self.message)


class InvalidTaskPriorityError(Exception):
    """Raised when an invalid task priority is provided"""
    def __init__(self, priority: str):
        self.priority = priority
        valid_priorities = [p.value for p in TaskPriority]
        self.message = f"Invalid task priority: {priority}. Valid priorities are: {', '.join(valid_priorities)}"
        super().__init__(self.message)


class PermissionDeniedError(Exception):
    """Raised when a user doesn't have permission to perform an action"""
    def __init__(self, message: str = "Not enough permissions"):
        self.message = message
        super().__init__(self.message)


def add_exception_handlers(app: FastAPI) -> None:
    """Add exception handlers to FastAPI app"""
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
            },
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Database error",
                "message": str(exc),
            },
        )
    
    @app.exception_handler(TaskNotFoundError)
    async def task_not_found_exception_handler(request: Request, exc: TaskNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )
    
    @app.exception_handler(UserNotFoundError)
    async def user_not_found_exception_handler(request: Request, exc: UserNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )
    
    @app.exception_handler(InvalidTaskStatusError)
    async def invalid_task_status_exception_handler(request: Request, exc: InvalidTaskStatusError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )
    
    @app.exception_handler(InvalidTaskPriorityError)
    async def invalid_task_priority_exception_handler(request: Request, exc: InvalidTaskPriorityError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )
    
    @app.exception_handler(PermissionDeniedError)
    async def permission_denied_exception_handler(request: Request, exc: PermissionDeniedError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": exc.message},
        )