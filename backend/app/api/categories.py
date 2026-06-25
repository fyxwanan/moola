from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.database import get_db
from app.models.category import CategoryCreate, CategoryResponse
from app.models.base import serialize_list, serialize_doc
from app.api.deps import get_current_user

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("", response_model=List[CategoryResponse])
async def list_categories(current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = str(current_user["_id"])
    
    # Query categories where owner_id is either None (system) or the current user's ID
    cursor = db["categories"].find({
        "$or": [
            {"owner_id": None},
            {"owner_id": ObjectId(user_id)}
        ]
    })
    categories = await cursor.to_list(length=100)
    return serialize_list(categories)

@router.post("", response_model=CategoryResponse)
async def create_category(
    category_in: CategoryCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    user_id = str(current_user["_id"])
    
    # Check if category with the same name and type already exists for this user (or system defaults)
    existing = await db["categories"].find_one({
        "name": category_in.name,
        "type": category_in.type,
        "$or": [
            {"owner_id": None},
            {"owner_id": ObjectId(user_id)}
        ]
    })
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category_in.name}' already exists."
        )
        
    doc = {
        "name": category_in.name,
        "type": category_in.type,
        "icon": category_in.icon,
        "color": category_in.color,
        "owner_id": ObjectId(user_id)
    }
    
    result = await db["categories"].insert_one(doc)
    doc["_id"] = result.inserted_id
    
    return serialize_doc(doc)

@router.delete("/{category_id}", response_model=dict)
async def delete_category(
    category_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    user_id = str(current_user["_id"])
    
    try:
        cat_obj_id = ObjectId(category_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID format"
        )
        
    # Check if the category exists and belongs to the user
    category = await db["categories"].find_one({"_id": cat_obj_id})
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
        
    if category["owner_id"] is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system default categories"
        )
        
    if str(category["owner_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
        
    # Delete the category
    await db["categories"].delete_one({"_id": cat_obj_id})
    return {"message": "Category deleted successfully"}
