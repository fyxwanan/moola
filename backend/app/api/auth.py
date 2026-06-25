from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Response
from bson import ObjectId
from app.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import UserRegister, UserLogin, UserResponse, UserUpdate
from app.models.base import serialize_doc
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=dict)
async def register(user_in: UserRegister):
    db = get_db()
    # Check if user already exists
    existing_user = await db["users"].find_one({"username": user_in.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Hash password and create user object
    hashed_password = get_password_hash(user_in.password)
    nickname = user_in.nickname if user_in.nickname else user_in.username
    email = user_in.email if user_in.email else ""
    
    user_doc = {
        "username": user_in.username,
        "nickname": nickname,
        "email": email,
        "password_hash": hashed_password,
        "avatar_url": "",
        "theme": "system",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    result = await db["users"].insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Generate token
    token = create_access_token(subject=user_id)
    
    user_doc["id"] = user_id
    del user_doc["_id"]
    del user_doc["password_hash"]
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_doc(user_doc)
    }

@router.post("/login", response_model=dict)
async def login(user_in: UserLogin, response: Response):
    db = get_db()
    # Find user
    user = await db["users"].find_one({"username": user_in.username})
    if not user or not verify_password(user_in.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    
    user_id = str(user["_id"])
    token = create_access_token(subject=user_id)
    
    # Expose authorization header as well
    response.headers["Authorization"] = f"Bearer {token}"
    response.headers["Access-Control-Expose-Headers"] = "Authorization"
    
    user_data = serialize_doc(user)
    if "password_hash" in user_data:
        del user_data["password_hash"]
        
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    user_data = serialize_doc(current_user)
    if "password_hash" in user_data:
        del user_data["password_hash"]
    return user_data

@router.put("/me", response_model=UserResponse)
async def update_me(user_in: UserUpdate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    update_data = {}
    
    if user_in.nickname is not None:
        update_data["nickname"] = user_in.nickname
    if user_in.email is not None:
        update_data["email"] = user_in.email
    if user_in.avatar_url is not None:
        update_data["avatar_url"] = user_in.avatar_url
    if user_in.theme is not None:
        update_data["theme"] = user_in.theme
    if user_in.password is not None:
        update_data["password_hash"] = get_password_hash(user_in.password)
        
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
        
        # Retrieve updated user
        updated_user = await db["users"].find_one({"_id": current_user["_id"]})
    else:
        updated_user = current_user
        
    user_data = serialize_doc(updated_user)
    if "password_hash" in user_data:
        del user_data["password_hash"]
    return user_data
