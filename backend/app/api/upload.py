from fastapi import APIRouter, UploadFile, File, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import Response
from bson import ObjectId
from app.database import get_db
from datetime import datetime

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    # Restrict uploads to image formats
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image uploads are allowed"
        )
        
    db = get_db()
    contents = await file.read()
    
    file_doc = {
        "filename": file.filename,
        "content_type": file.content_type,
        "data": contents,  # Saved as BSON binary bytes
        "created_at": datetime.utcnow(),
        "last_accessed_at": datetime.utcnow()
    }
    
    result = await db["files"].insert_one(file_doc)
    file_id = str(result.inserted_id)
    
    # Return relative URL pattern
    file_url = f"/api/upload/{file_id}"
    
    return {"url": file_url, "id": file_id}

async def update_last_accessed(db, file_obj_id: ObjectId):
    try:
        await db["files"].update_one(
            {"_id": file_obj_id},
            {"$set": {"last_accessed_at": datetime.utcnow()}}
        )
    except Exception:
        pass

@router.get("/{file_id}")
async def get_file(file_id: str, request: Request, background_tasks: BackgroundTasks):
    db = get_db()
    
    try:
        file_obj_id = ObjectId(file_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format"
        )
        
    file_doc = await db["files"].find_one({"_id": file_obj_id})
    if not file_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
        
    etag = f'W/"{file_id}"'
    
    # Update access time in background
    background_tasks.add_task(update_last_accessed, db, file_obj_id)
    
    # Check conditional cache headers
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)
        
    return Response(
        content=file_doc["data"],
        media_type=file_doc["content_type"],
        headers={
            "Cache-Control": "public, max-age=31536000",
            "ETag": etag
        }
    )
