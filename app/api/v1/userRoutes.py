from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional
from app.schemas.user import ChangePasswordDto, UpdateProfileDto
from app.database.models import User, Role
from app.utils.security import verify_password, get_password_hash
from app.utils import dbSession, apiResponse
from app.database.repositories.user import create_user
from app.database.repositories import (
    require_authenticated,require_permission  
    )
from app.database.repositories import update_user
from app.schemas.rbac import PermissionEnum as Permissions, RoleEnum as Roles, RoleAssign
from fastapi import APIRouter, Request, HTTPException, Depends
from ipaddress import ip_address as ip
router = APIRouter()
admin_router = APIRouter(prefix="/admin", tags=["Admin"])
http_bearer = HTTPBearer()

# Regular User Endpoints

@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(require_authenticated())
):
    """Get current user's profile (authenticated users only)"""
    return current_user


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordDto,
    user: User = Depends(require_authenticated()),
    db: Session = Depends(dbSession),
):
    """Change own password"""
    if not verify_password(payload.old_password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect old password")

    user.password = get_password_hash(payload.new_password)
    db.commit()
    return apiResponse("success", "Password changed successfully")



@router.patch("/me")
async def update_my_profile(
    payload: UpdateProfileDto,
    request: Request,  # to get IP
    user: User = Depends(require_authenticated()),
    db: Session = Depends(dbSession),
):
    """Update own profile"""
    update_data = payload.model_dump(exclude_unset=True)

    # Convert avatar_url to string if present
    if "avatar_url" in update_data:
        update_data["avatar_url"] = str(update_data["avatar_url"])

    # Apply payload values to user object
    for key, value in update_data.items():
        setattr(user, key, value)

    ip_address = ip.get()
    # Get IP address from request
    ip_address = ip_address if ip_address else request.client.host

    # Use central update_user function
    updated_user = update_user(db, user, ip_address)

    return apiResponse(
        "success",
        "Profile updated successfully",
        {key: getattr(updated_user, key) for key in update_data.keys()},
    )

# Admin Endpoints

@admin_router.get("/users")
async def admin_list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(require_permission(Permissions.READ_USER)),
    db: Session = Depends(dbSession)
):
    """List all users (admin only)"""
    query = db.query(User)
    if search:
        query = query.filter(
            (User.full_name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
    
    total = query.count()
    users = query.offset((page - 1) * limit).limit(limit).all()
    
    return apiResponse(
        "success",
        "Users retrieved",
        {
            "users": users,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    )


@admin_router.get("/users/{user_id}")
async def admin_get_user(
    user_id: int,
    current_user: User = Depends(require_permission(Permissions.READ_USER)),
    db: Session = Depends(dbSession)
):
    """Get any user details"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return apiResponse("success", "User retrieved", {"user": user})


@admin_router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: int,
    payload: UpdateProfileDto,
    current_user: User = Depends(require_permission(Permissions.UPDATE_USER)),
    db: Session = Depends(dbSession)
):
    """Update any user"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    return apiResponse("success", "User updated")


@admin_router.patch("/users/{user_id}/activate")
async def admin_activate_user(
    user_id: int,
    current_user: User = Depends(require_permission(Permissions.UPDATE_USER)),
    db: Session = Depends(dbSession)
):
    """Activate user account"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    db.commit()
    return apiResponse("success", "User activated")

