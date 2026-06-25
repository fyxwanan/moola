from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from bson import ObjectId
from app.database import get_db
from app.models.user import UserResponse
from app.models.base import serialize_list
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/search", response_model=List[dict])
async def search_users(
    q: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    current_id = current_user["_id"]
    
    query = {"_id": {"$ne": current_id}} # Exclude current user from searches
    
    if q and q.strip():
        search_str = q.strip()
        # Case-insensitive regex fuzzy match
        regex_query = {"$regex": search_str, "$options": "i"}
        query["$or"] = [
            {"username": regex_query},
            {"nickname": regex_query},
            {"email": regex_query}
        ]
        
        cursor = db["users"].find(query).limit(10)
    else:
        # Default recommendation: list up to 10 active users
        cursor = db["users"].find(query).sort("created_at", -1).limit(10)
        
    users = await cursor.to_list(length=10)
    
    # Format return list (exclude password hashes)
    formatted_users = []
    for u in users:
        formatted_users.append({
            "id": str(u["_id"]),
            "username": u["username"],
            "nickname": u.get("nickname") or u["username"],
            "email": u.get("email") or "",
            "avatar_url": u.get("avatar_url") or ""
        })
        
    return formatted_users
