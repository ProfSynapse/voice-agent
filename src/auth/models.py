"""
Authentication Models Module

This module defines the data models for authentication.
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


class UserRole(Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"


@dataclass
class User:
    """User model."""
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    role: UserRole = UserRole.USER
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        Create a User instance from a dictionary.
        
        Args:
            data: Dictionary containing user data
            
        Returns:
            User instance
        """
        role = data.get("role", "user")
        if isinstance(role, str):
            role = UserRole(role)
            
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            
        return cls(
            id=data.get("id", ""),
            email=data.get("email", ""),
            full_name=data.get("full_name", ""),
            avatar_url=data.get("avatar_url"),
            role=role,
            created_at=created_at,
            updated_at=updated_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert User instance to a dictionary.
        
        Returns:
            Dictionary representation of the user
        """
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "role": self.role.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class AuthResult:
    """Authentication result model."""
    success: bool
    user: Optional[User] = None
    session: Optional[Dict[str, Any]] = None
    error: Optional[str] = None