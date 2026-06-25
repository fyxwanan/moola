from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    nickname: Optional[str] = Field(default="", max_length=50)
    email: Optional[str] = Field(default="", max_length=100)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    nickname: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: Optional[str] = "system"
    created_at: datetime

class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    theme: Optional[str] = None
