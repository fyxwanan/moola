from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from app.models.category import CategoryResponse

class RecordCreate(BaseModel):
    amount: float = Field(..., gt=0)
    type: Literal["income", "expense"]
    category_id: str
    note: Optional[str] = Field("", max_length=500)
    record_date: datetime
    project_id: Optional[str] = None # null if personal ledger
    images: Optional[list[str]] = []

class RecordUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[Literal["income", "expense"]] = None
    category_id: Optional[str] = None
    note: Optional[str] = Field(None, max_length=500)
    record_date: Optional[datetime] = None
    images: Optional[list[str]] = None

class RecordResponse(BaseModel):
    id: str
    user_id: str
    project_id: Optional[str] = None
    amount: float
    type: str
    category_id: str
    note: Optional[str] = ""
    record_date: datetime
    images: list[str] = []
    created_at: datetime
    updated_at: datetime
    
    # Optional populated fields for UI convenience
    category: Optional[CategoryResponse] = None
    creator_nickname: Optional[str] = None
    creator_avatar_url: Optional[str] = None
