# Task Management API

A simple task management API built with FastAPI and SQLModel.

## Features

- User management
- Task creation and management
- RESTful API design
- Async database operations
- API documentation with Swagger and ReDoc

## Requirements

- Python 3.7+
- FastAPI
- SQLModel
- Uvicorn

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/moparthi-sid/test-123.git
   cd test-123
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

Start the application with:

```
python main.py
```

Alternatively, you can use the Uvicorn command:

```
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Tasks

- `GET /tasks`: Get all tasks
- `GET /tasks/{task_id}`: Get a specific task
- `POST /tasks`: Create a new task
- `PATCH /tasks/{task_id}`: Update a task
- `DELETE /tasks/{task_id}`: Delete a task

### Users

- `GET /users`: Get all users
- `GET /users/{user_id}`: Get a specific user
- `POST /users`: Create a new user
- `PATCH /users/{user_id}`: Update a user
- `DELETE /users/{user_id}`: Delete a user