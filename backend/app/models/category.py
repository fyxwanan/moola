from typing import Optional, Literal
from pydantic import BaseModel, Field

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    type: Literal["income", "expense"]
    icon: str = Field("HelpCircle") # Lucide Icon name
    color: str = Field("#6B7280") # Color code

class CategoryResponse(BaseModel):
    id: str
    name: str
    type: str
    icon: str
    color: str
    owner_id: Optional[str] = None # None means system category
