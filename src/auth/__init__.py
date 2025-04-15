"""
Authentication Package

This package provides authentication functionality using Supabase.
"""

from src.auth.models import User, UserRole, AuthResult
from src.auth.service import AuthService, create_auth_service
from src.auth.security import AuthSecurityService, create_auth_security_service
from src.auth.api_key import APIKeyManager, create_api_key_manager

__all__ = [
    # Models
    "User",
    "UserRole",
    "AuthResult",
    
    # Core authentication
    "AuthService",
    "create_auth_service",
    
    # Security services
    "AuthSecurityService",
    "create_auth_security_service",
    
    # API key management
    "APIKeyManager",
    "create_api_key_manager"
]