import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_db_and_tables
from app.auth.router import router as auth_router
from app.errors import add_exception_handlers
from app.routers import tasks, users

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    logger.info("Creating database tables...")
    await create_db_and_tables()
    logger.info("Database tables created")
    
    yield
    
    # Clean up resources if needed
    logger.info("Shutting down application")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Task Management API",
    description="A simple task management API built with FastAPI and SQLModel",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(tasks.router)
app.include_router(users.router)

# Add custom exception handlers
add_exception_handlers(app)


@app.get("/")
async def root():
    """Root endpoint that returns API information"""
    return {
        "message": "Welcome to Task Management API",
        "docs": "/docs",
        "redoc": "/redoc",
    }