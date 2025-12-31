from enum import Enum
from pydantic import BaseModel
from typing import List, Optional



# Permissions
class PermissionEnum(str, Enum):
    # User management
    CREATE_USER = "users.create"
    READ_USER = "users.read"
    UPDATE_USER = "users.update"
    DELETE_USER = "users.delete"

    # Role management
    CREATE_ROLE = "role.create"
    READ_ROLE = "role.read"
    UPDATE_ROLE = "role.update"
    DELETE_ROLE = "role.delete"

    # Content management
    CREATE_CONTENT = "documents.create"
    READ_CONTENT = "documents.read"
    UPDATE_CONTENT = "documents.update"
    DELETE_CONTENT = "documents.delete"

    # API / Assets / Agents
    CREATE_API = "api.create"
    READ_API = "api.read"
    DELETE_API = "api.delete"

    CREATE_ASSET = "assets.create"
    READ_ASSET = "assets.read"
    UPDATE_ASSET = "assets.update"
    DELETE_ASSET = "assets.delete"

    CREATE_AGENT = "agent.create"
    READ_AGENT = "agent.read"
    UPDATE_AGENT = "agent.update"
    DELETE_AGENT = "agent.delete"

    # Notifications
    CREATE_NOTIFICATION = "notification.create"
    READ_NOTIFICATION = "notification.read"
    UPDATE_NOTIFICATION = "notification.update"
    DELETE_NOTIFICATION = "notification.delete"
    DELETE_OWN_NOTIFICATION = "own_notification.delete"

    # Analytics / System
    CREATE_ANALYTICS = "analytics.create"
    READ_ANALYTICS = "analytics.read"
    UPDATE_ANALYTICS = "analytics.update"
    DELETE_ANALYTICS = "analytics.delete"

    VIEW_REPORTS = "analytics.reports"
    VIEW_LOGS = "system.logs"

    # Own profile management
    CREATE_OWN_USER = "own_user.create"
    READ_OWN_USER = "own_user.read"
    UPDATE_OWN_USER = "own_user.update"
    DELETE_OWN_USER = "own_user.delete"



# Roles
class RoleEnum(str, Enum):
    SUPERUSER = "superuser"
    ADMIN = "admin"
    USER = "user"



# DTOs
class RoleCreate(BaseModel):
    name: RoleEnum
    permissions: List[PermissionEnum]


class RoleAssign(BaseModel):
    user_id: int
    role: RoleEnum


class PermissionCreate(BaseModel):
    name: PermissionEnum


class PermissionResponse(BaseModel):
    id: Optional[int] = None
    codename: str
    description: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "exclude_none": True,
    }


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[PermissionResponse] = []

    class Config:
        from_attributes = True


class UpdateUserRolesDto(BaseModel):
    role_names: Optional[List[str]] = []
    is_admin: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UpdateUserStatus(BaseModel):
    is_active: Optional[bool] = None
    role_names: Optional[List[str]] = []
    is_admin: Optional[bool] = None
    is_superuser: Optional[bool] = None
