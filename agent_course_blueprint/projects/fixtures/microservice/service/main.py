"""Microservice main module"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="User Service", version="1.0.0")

# In-memory storage
users_db = {}
next_id = 1


class User(BaseModel):
    name: str
    email: str
    age: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/users", response_model=list[UserResponse])
def list_users():
    """List all users"""
    return list(users_db.values())


@app.post("/api/users", response_model=UserResponse)
def create_user(user: User):
    """Create a new user"""
    global next_id
    user_data = UserResponse(id=next_id, **user.dict())
    users_db[next_id] = user_data
    next_id += 1
    return user_data


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    """Get user by ID"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
