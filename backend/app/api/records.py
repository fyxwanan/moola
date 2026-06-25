from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from bson import ObjectId
from app.database import get_db
from app.models.record import RecordCreate, RecordResponse, RecordUpdate
from app.models.base import serialize_doc
from app.api.deps import get_current_user

router = APIRouter(prefix="/records", tags=["records"])

async def populate_records(records_list: list, db) -> list:
    """Helper to populate category info and user nicknames for a list of record documents."""
    if not records_list:
        return []
        
    # Get distinct category and user IDs to batch fetch
    category_ids = list({r["category_id"] for r in records_list if "category_id" in r})
    user_ids = list({r["user_id"] for r in records_list if "user_id" in r})
    
    # Query categories
    categories_map = {}
    if category_ids:
        cursor = db["categories"].find({"_id": {"$in": category_ids}})
        cats = await cursor.to_list(length=1000)
        for cat in cats:
            categories_map[cat["_id"]] = serialize_doc(cat)
            
    # Query user nicknames and avatars
    users_map = {}
    if user_ids:
        cursor = db["users"].find({"_id": {"$in": user_ids}})
        usrs = await cursor.to_list(length=1000)
        for u in usrs:
            users_map[u["_id"]] = {
                "nickname": u.get("nickname") or u.get("username", "Unknown"),
                "avatar_url": u.get("avatar_url")
            }
            
    populated = []
    for r in records_list:
        r_serialized = serialize_doc(r)
        
        # Ensure images is always present
        if "images" not in r_serialized or r_serialized["images"] is None:
            r_serialized["images"] = []
            
        # Resolve category
        cat_id = r.get("category_id")
        if cat_id in categories_map:
            r_serialized["category"] = categories_map[cat_id]
            
        # Resolve creator nickname & avatar
        u_id = r.get("user_id")
        if u_id in users_map:
            r_serialized["creator_nickname"] = users_map[u_id]["nickname"]
            r_serialized["creator_avatar_url"] = users_map[u_id]["avatar_url"]
            
        populated.append(r_serialized)
        
    return populated

@router.post("", response_model=RecordResponse)
async def create_record(
    record_in: RecordCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    user_id = current_user["_id"]
    
    # Verify category
    try:
        cat_obj_id = ObjectId(record_in.category_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID format"
        )
        
    category = await db["categories"].find_one({
        "_id": cat_obj_id,
        "$or": [
            {"owner_id": None},
            {"owner_id": user_id}
        ]
    })
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found or not owned by you"
        )
        
    # Verify project if provided
    proj_obj_id = None
    if record_in.project_id:
        try:
            proj_obj_id = ObjectId(record_in.project_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project ID format"
            )
            
        project = await db["projects"].find_one({"_id": proj_obj_id})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project not found"
            )
            
        # User must be a member
        if user_id not in project.get("members", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project"
            )
            
    doc = {
        "user_id": user_id,
        "project_id": proj_obj_id,
        "amount": record_in.amount,
        "type": record_in.type,
        "category_id": cat_obj_id,
        "note": record_in.note or "",
        "record_date": record_in.record_date,
        "images": record_in.images or [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db["records"].insert_one(doc)
    doc["_id"] = result.inserted_id
    
    # Populate the response
    populated = await populate_records([doc], db)
    return populated[0]

@router.get("", response_model=List[RecordResponse])
async def list_records(
    project_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    category_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    user_id = current_user["_id"]
    
    query = {}
    
    # 1. Project filtering
    if project_id:
        # Check permission for project records
        try:
            proj_obj_id = ObjectId(project_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project ID format"
            )
            
        project = await db["projects"].find_one({"_id": proj_obj_id})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
            
        if user_id not in project.get("members", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not a member of this project"
            )
        query["project_id"] = proj_obj_id
    else:
        # Default to user's personal bills (where project_id is None and user_id is the current user)
        query["project_id"] = None
        query["user_id"] = user_id
        
    # 2. Date filtering
    if start_date or end_date:
        query["record_date"] = {}
        if start_date:
            query["record_date"]["$gte"] = start_date
        if end_date:
            query["record_date"]["$lte"] = end_date
            
    # 3. Category filtering
    if category_id:
        try:
            query["category_id"] = ObjectId(category_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category ID format"
            )
            
    # 4. Type filtering (income/expense)
    if type:
        if type not in ["income", "expense"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Type must be either 'income' or 'expense'"
            )
        query["type"] = type
        
    cursor = db["records"].find(query).sort("record_date", -1)
    records = await cursor.to_list(length=2000)
    
    populated = await populate_records(records, db)
    return populated

@router.put("/{record_id}", response_model=RecordResponse)
async def update_record(
    record_id: str,
    record_in: RecordUpdate,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    user_id = current_user["_id"]
    
    try:
        rec_obj_id = ObjectId(record_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid record ID format"
        )
        
    record = await db["records"].find_one({"_id": rec_obj_id})
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )
        
    # Authorization checks:
    # If project-level: any project member can view and edit
    # If personal-level: only owner can view and edit
    project_id = record.get("project_id")
    if project_id:
        project = await db["projects"].find_one({"_id": project_id})
        if not project or user_id not in project.get("members", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to modify this project record"
            )
    else:
        if record.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot edit someone else's personal record"
            )
            
    update_data = {}
    if record_in.amount is not None:
        update_data["amount"] = record_in.amount
    if record_in.type is not None:
        update_data["type"] = record_in.type
    if record_in.note is not None:
        update_data["note"] = record_in.note
    if record_in.record_date is not None:
        update_data["record_date"] = record_in.record_date
    if record_in.images is not None:
        update_data["images"] = record_in.images
        
    if record_in.category_id is not None:
        try:
            cat_obj_id = ObjectId(record_in.category_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category ID format"
            )
            
        # Verify category exists and is owned by the modifier or system
        category = await db["categories"].find_one({
            "_id": cat_obj_id,
            "$or": [
                {"owner_id": None},
                {"owner_id": user_id}
            ]
        })
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or not owned by you"
            )
        update_data["category_id"] = cat_obj_id
        
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await db["records"].update_one(
            {"_id": rec_obj_id},
            {"$set": update_data}
        )
        record = await db["records"].find_one({"_id": rec_obj_id})
        
    populated = await populate_records([record], db)
    return populated[0]

@router.delete("/{record_id}", response_model=dict)
async def delete_record(
    record_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    user_id = current_user["_id"]
    
    try:
        rec_obj_id = ObjectId(record_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid record ID format"
        )
        
    record = await db["records"].find_one({"_id": rec_obj_id})
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )
        
    # Authorization checks:
    # If project-level: any project member can delete
    # If personal: only creator can delete
    project_id = record.get("project_id")
    if project_id:
        project = await db["projects"].find_one({"_id": project_id})
        if not project or user_id not in project.get("members", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to delete this project record"
            )
    else:
        if record.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot delete someone else's personal record"
            )
            
    await db["records"].delete_one({"_id": rec_obj_id})
    return {"message": "Record deleted successfully"}
