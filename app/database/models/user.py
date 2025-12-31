
import uuid
from typing import Set, Optional, List
from fastapi import Depends, HTTPException, status
from sqlalchemy import Column, String, Boolean, DateTime, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column, Session
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, String, Table, Text, DateTime, CheckConstraint
)
import enum
from enum import Enum
from app.database import Base
# Assuming you have these imports from your existing code
# from app.database import Base


class CountryEnum(str, enum.Enum):
    NIGERIA = "NG"
    OTHERS = "OTHERS"


# Your existing tables
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)

# Enhanced User model with RBAC methods
class User(Base):
    __tablename__ = "users"

    id                      = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email                   = Column(String(255), unique=True, index=True)
    password                = Column(String(255), nullable=True)
    full_name               = Column(String(255), nullable=True)
    phone_number            = Column(String(20), nullable=False)
    country_location        = Column(String(255), nullable=True)
    is_active               = Column(Boolean, default=True)
    terms_agreed            = Column(Boolean, default=True)
    social_account_id       = Column(String(255), nullable=True)
    avatar_url              = Column(String, nullable=True)
    theme                   = Column(String, default="light")
    language                = Column(String, default="english")
    email_verified          = Column(Boolean, default=False)
    is_superuser            = Column(Boolean, default=False, nullable=False)
    is_admin                = Column(Boolean, default=False)
    two_factor_secret       = Column(String, nullable=True)  # base32 TOTP key
    two_factor_enabled      = Column(Boolean, default=False)
    must_change_password    = Column(Boolean, default=False)
    login_provider          = Column(String(255), nullable=True)
    token_version           = Column(Integer, default=0)
    created_at              = Column(DateTime, nullable=False, server_default=func.now())
    updated_at              = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    documents               = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    user_otps               = relationship("UserOtp", back_populates="user", cascade="all, delete")

    # RBAC relationships
    roles: Mapped[list["Role"]] = relationship(secondary=user_roles, back_populates="users", lazy="selectin")
    
    # Ensure exactly one tier is true
    __table_args__ = (
        CheckConstraint(
            "(is_superuser::int + is_admin::int) IN (0, 1)",
            name="tier_check"
        ),
    )

    @property
    def tier(self) -> str:
        """Return the user's tier as a string."""
        if self.is_superuser:
            return "superuser"
        if self.is_admin:
            return "admin"
        return "user"

    def has_permission(self, permission_codename: str) -> bool:
        """
        Check if user has a specific permission.
        Priority:
          1. Superuser = all permissions
          2. Admin = all role-based permissions + admin flag override
          3. Regular user = only role-based permissions
        """
        if not self.is_active:
            return False

        # Superuser has everything
        if self.is_superuser:
            return True

        # Admin inherits all assigned role permissions
        if self.is_admin and permission_codename in self.get_all_permissions():
            return True

        # Check role-based permissions
        return permission_codename in self.get_all_permissions()

    def get_all_permissions(self) -> Set[str]:
        """Return all unique permissions from user's roles."""
        return {
            permission.codename
            for role in self.roles
            for permission in role.permissions
        }

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role (case-insensitive)."""
        if role_name.lower() == "superuser" and self.is_superuser:
            return True
        if role_name.lower() == "admin" and self.is_admin:
            return True
        return any(role.name.lower() == role_name.lower() for role in self.roles)

    def is_owner_of_resource(self, resource_user_id: uuid.UUID) -> bool:
        """Check if user owns a resource."""
        return self.id == resource_user_id

    def can_manage_user(self, target_user: "User") -> bool:
        """
        Check if current user can manage another user.
        Rules:
          - Superuser can manage anyone.
          - Admin can manage non-superusers.
          - A user can manage their own account.
        """
        if self.is_superuser:
            return True
        if self.is_admin and not target_user.is_superuser:
            return True
        return self.id == target_user.id

    def non_sensitive(self):
        """Serialize the model to dict excluding sensitive fields like password/2FA secret."""
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "phone_number": self.phone_number,
            "country_location": self.country_location,
            "is_active": self.is_active,
            "terms_agreed": self.terms_agreed,
            "social_account_id": self.social_account_id,
            "avatar_url": self.avatar_url,
            "theme": self.theme,
            "language": self.language,
            "email_verified": self.email_verified,
            "login_provider": self.login_provider,
            "tier": self.tier,
            "roles": [{"name": role.name, "description": role.description} for role in self.roles],
            "permissions": list(self.get_all_permissions())
        }

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str | None] = mapped_column(Text)

    users: Mapped[list["User"]] = relationship(
        secondary=user_roles, back_populates="roles"
    )
    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permissions, back_populates="roles", lazy="selectin"
    )


class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codename: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    roles: Mapped[list["Role"]] = relationship(
        secondary=role_permissions, back_populates="permissions"
    )
    