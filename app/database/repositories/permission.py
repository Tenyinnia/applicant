from typing import Set, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.future import select
# from app.utils import get_current_user
from app.schemas import PermissionEnum, RoleEnum
from app.database.models import User, Role, Permission
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils import dbSession
from .auth import get_current_user
# from app.utils import verify_jwt
from sqlalchemy.ext.asyncio import AsyncSession

http_bearer = HTTPBearer()

# Permission Resolution
def get_user_permissions(user: User) -> Set[str]:
    """Get all permissions for a user based on DB roles + flags."""
    if not user.is_active:
        return set()

    permissions = set()

    # If superuser → all permissions from enum
    if user.is_superuser:
        return {p.value for p in PermissionEnum}

    # Add permissions from assigned roles
    for role in user.roles:
        for perm in role.permissions:
            permissions.add(perm.codename)

    return permissions


def has_permission(user: User, permission: str) -> bool:
    """Check if a user has a specific permission."""
    return user.is_active and permission in get_user_permissions(user)


def has_role(user: User, role: str) -> bool:
    """Check if user has a role or higher."""
    if not user.is_active:
        return False

    role = role.lower()

    # Flag overrides
    if role == RoleEnum.SUPERUSER.value and user.is_superuser:
        return True
    if role == RoleEnum.ADMIN.value and user.is_admin:
        return True
    if role == RoleEnum.USER.value:
        return True

    # DB role check
    return any(r.name.lower() == role for r in user.roles)


def is_resource_owner(user: User, resource_user_id) -> bool:
    return str(user.id) == str(resource_user_id)



#RBAC Manager
class RBACManager:
    def __init__(self, db: Session):
        self.db = db

    def get_role_by_name(self, name: str) -> Optional[Role]:
        return self.db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()

    def get_permission_by_codename(self, codename: str) -> Optional[Permission]:
        return self.db.execute(select(Permission).where(Permission.codename == codename)).scalar_one_or_none()

    def create_role(self, name: str, description: str = None) -> Role:
        if existing := self.get_role_by_name(name):
            return existing
        role = Role(name=name, description=description)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def create_permission(self, codename: str, description: str = None) -> Permission:
        if existing := self.get_permission_by_codename(codename):
            return existing
        permission = Permission(codename=codename, description=description)
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission

    def assign_role_to_user(self, user: User, role: Role):
        if role not in user.roles:
            user.roles.append(role)
            self.db.commit()

    def assign_permission_to_role(self, role: Role, permission: Permission):
        if permission not in role.permissions:
            role.permissions.append(permission)
            self.db.commit()


async def get_or_create_admin_role(session: AsyncSession) -> Role:
    """Ensure an admin role exists; if not, create it with default permissions"""
    role = (await session.execute(select(Role).where(Role.name == "admin"))).scalar_one_or_none()
    if role:
        return role

    role = Role(name="admin", description="Full system access")
    default_permissions = [
        Permission(codename="users.read"),
        Permission(codename="users.write"),
        Permission(codename="roles.write"),
    ]
    role.permissions.extend(default_permissions)

    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role

# Guards (FastAPI Dependencies)
# def require_permission(permission: str):
#     def _guard(user: User = Depends(get_current_user)):
#         if not has_permission(user, permission):
#             raise HTTPException(status_code=403, detail=f"Permission '{permission}' required")
#         return user
#     return _guard


# def require_role(role: str):
#     def _guard(user: User = Depends(get_current_user)):
#         if not has_role(user, role):
#             raise HTTPException(status_code=403, detail=f"Role '{role}' or higher required")
#         return user
#     return _guard


# def require_superuser():
#     return require_role(RoleEnum.SUPERUSER.value)


def require_admin(
    db: Session = Depends(dbSession),
    current_user: User = Depends(get_current_user)
):
    """Require explicit 'admin' or superuser flag/role."""
    if current_user.is_superuser or current_user.is_admin:
        return current_user

    if any(role.name.lower() == "admin" for role in current_user.roles):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions"
    )


def require_authenticated():
    """Require any authenticated + active user."""
    def _guard(user: User = Depends(get_current_user)):
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account disabled. Login and try again."
            )
        return user
    return _guard


def require_superadmin(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized"
        )
    return current_user 

def require_admin_or_superadmin(
    db: Session = Depends(dbSession),
    current_user: User = Depends(get_current_user),
):
    """Allow access if user is either a superuser or has the 'admin' role."""
    if current_user.is_superuser or current_user.is_admin:
        return current_user

    if any(role.name.lower() in ["admin", "superuser"] for role in current_user.roles):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin or Superadmin privileges required",
    )

def require_permission(permission: str):
    def _guard(user: User = Depends(get_current_user)):
        if not has_permission(user, permission):
            raise HTTPException(status_code=403, detail=f"Permission '{permission}' required")
        return user
    return _guard