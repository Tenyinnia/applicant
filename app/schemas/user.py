from pydantic import BaseModel, HttpUrl
from typing import Optional, Literal
from .auth import RegistrationDto
from .rbac import RoleResponse, PermissionResponse
from typing import List
from uuid import UUID
from datetime import datetime
from .user_api import ApiKeyResponse, UsageStatsResponse

class UpdateProfileDto(BaseModel):
    full_name: Optional[str]
    theme: Optional[Literal["light", "dark", "auto"]]
    language: Optional[str]
    country_location: Optional[str]
    avatar_url: Optional[HttpUrl]
    

class ChangePasswordDto(BaseModel):
    old_password:   str
    new_password:   str

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    is_admin: bool
    roles: List[RoleResponse] = []

    class Config:
        from_attributes = True
        
class ActivityLogResponse(BaseModel):
    id: str
    action_type: str
    description: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status_code: Optional[int] = None
    endpoint: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    response_time_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
    
class UserDetailResponse(UserResponse):
    api_keys: List[ApiKeyResponse]
    usage_stats: UsageStatsResponse
    activity_logs: List[ActivityLogResponse] = []
    

