from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class MemberDetail(BaseModel):
    id: str
    username: str
    nickname: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    members: List[str] = [] # list of user ids
    member_details: Optional[List[MemberDetail]] = None
    created_at: datetime
    updated_at: datetime

class AddMemberRequest(BaseModel):
    username: str
