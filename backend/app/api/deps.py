from fastapi import Depends, HTTPException, status, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from app.database import get_db
from app.core.security import decode_token, create_access_token

security_scheme = HTTPBearer(auto_error=True)

async def get_current_user(
    response: Response,
    token_credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> dict:
    token = token_credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject",
        )
    
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )
        
    db = get_db()
    user = await db["users"].find_one({"_id": obj_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist",
        )
        
    # Sliding token refresh: Generate a fresh token for 30 days and send in response headers
    new_token = create_access_token(subject=user_id)
    response.headers["Authorization"] = f"Bearer {new_token}"
    response.headers["Access-Control-Expose-Headers"] = "Authorization"
    
    return user
