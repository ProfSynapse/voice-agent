"""
Authentication Package

This package provides authentication functionality using Supabase.
"""

from src.auth.models import User, UserRole, AuthResult
from src.auth.service import AuthService, create_auth_service

__all__ = [
    "User",
    "UserRole",
    "AuthResult",
    "AuthService",
    "create_auth_service"
]