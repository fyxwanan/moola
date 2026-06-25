from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.database import get_db
from app.models.project import ProjectCreate, ProjectResponse, ProjectUpdate, AddMemberRequest
from app.models.base import serialize_list, serialize_doc
from app.api.deps import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])

async def populate_member_details(project_doc: dict, db) -> dict:
    if not project_doc:
        return project_doc
    member_ids = project_doc.get("members", [])
    member_details = []
    for m_id in member_ids:
        try:
            m_obj_id = ObjectId(m_id) if isinstance(m_id, str) else m_id
        except Exception:
            continue
        user_doc = await db["users"].find_one({"_id": m_obj_id})
        if user_doc:
            member_details.append({
                "id": str(user_doc["_id"]),
                "username": user_doc.get("username", ""),
                "nickname": user_doc.get("nickname", "") or user_doc.get("username", ""),
                "email": user_doc.get("email"),
                "avatar_url": user_doc.get("avatar_url")
            })
    project_doc["member_details"] = member_details
    return project_doc

@router.get("", response_model=List[ProjectResponse])
async def list_projects(current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = current_user["_id"]
    
    # Query projects where the user is a member (members array contains user_id)
    cursor = db["projects"].find({"members": user_id})
    projects = await cursor.to_list(length=100)
    
    populated_projects = []
    for p in projects:
        p_pop = await populate_member_details(p, db)
        populated_projects.append(serialize_doc(p_pop))
    return populated_projects

@router.post("", response_model=ProjectResponse)
async def create_project(
    project_in: ProjectCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    user_id = current_user["_id"]
    
    doc = {
        "name": project_in.name,
        "description": project_in.description or "",
        "owner_id": user_id,
        "members": [user_id], # Creator is the first member
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    result = await db["projects"].insert_one(doc)
    doc["_id"] = result.inserted_id
    
    doc_pop = await populate_member_details(doc, db)
    return serialize_doc(doc_pop)

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    user_id = current_user["_id"]
    
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
        
    project_pop = await populate_member_details(project, db)
    return serialize_doc(project_pop)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    user_id = current_user["_id"]
    
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
        
    # Check authorization: Only owner can update project metadata
    if project.get("owner_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can update project details"
        )
        
    update_data = {}
    if project_in.name is not None:
        update_data["name"] = project_in.name
    if project_in.description is not None:
        update_data["description"] = project_in.description
        
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await db["projects"].update_one(
            {"_id": proj_obj_id},
            {"$set": update_data}
        )
        project = await db["projects"].find_one({"_id": proj_obj_id})
        
    project_pop = await populate_member_details(project, db)
    return serialize_doc(project_pop)

@router.delete("/{project_id}", response_model=dict)
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    user_id = current_user["_id"]
    
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
        
    # Check authorization: Only owner can delete project
    if project.get("owner_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can delete this project"
        )
        
    # Delete project
    await db["projects"].delete_one({"_id": proj_obj_id})
    
    # Cascade delete records under this project
    await db["records"].delete_many({"project_id": proj_obj_id})
    
    return {"message": "Project and its records deleted successfully"}

@router.post("/{project_id}/members", response_model=ProjectResponse)
async def add_project_member(
    project_id: str,
    member_in: AddMemberRequest,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    user_id = current_user["_id"]
    
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
        
    # Check authorization: Only project members can invite other people (owner or existing members)
    # The requirement is: "只要在同一个项目下的用户，都可以查看和修改项目下的账单", let's restrict adding members to members of the project.
    if user_id not in project.get("members", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You must be a member of the project to add new members"
        )
        
    # Find user to invite
    invitee = await db["users"].find_one({"username": member_in.username})
    if not invitee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username '{member_in.username}' not found"
        )
        
    invitee_id = invitee["_id"]
    if invitee_id in project.get("members", []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this project"
        )
        
    # Add to members list
    await db["projects"].update_one(
        {"_id": proj_obj_id},
        {
            "$push": {"members": invitee_id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    updated_project = await db["projects"].find_one({"_id": proj_obj_id})
    project_pop = await populate_member_details(updated_project, db)
    return serialize_doc(project_pop)

@router.delete("/{project_id}/members/{member_id}", response_model=ProjectResponse)
async def remove_project_member(
    project_id: str,
    member_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    user_id = current_user["_id"]
    
    try:
        proj_obj_id = ObjectId(project_id)
        memb_obj_id = ObjectId(member_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project/member ID format"
        )
        
    project = await db["projects"].find_one({"_id": proj_obj_id})
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
        
    owner_id = project.get("owner_id")
    
    # Check authorization:
    # 1. Owner can remove anyone except themselves.
    # 2. Members can remove themselves (leave project).
    is_owner = (user_id == owner_id)
    is_self_removal = (user_id == memb_obj_id)
    
    if not (is_owner or is_self_removal):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can remove members, or you can remove yourself"
        )
        
    if memb_obj_id == owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the owner of the project"
        )
        
    if memb_obj_id not in project.get("members", []):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this project"
        )
        
    # Remove member
    await db["projects"].update_one(
        {"_id": proj_obj_id},
        {
            "$pull": {"members": memb_obj_id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    # Also clean up records: no cascade for user bills, we keep them but owner field points to removed user.
    # If the user leaves, their project bills remain but they lose access.
    
    updated_project = await db["projects"].find_one({"_id": proj_obj_id})
    project_pop = await populate_member_details(updated_project, db)
    return serialize_doc(project_pop)
