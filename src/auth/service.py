"""
Authentication Service Module

This module provides the authentication service for the application.
"""

import re
import logging
from typing import Optional, Dict, Any, List, Tuple

from supabase import Client
from loguru import logger

from src.auth.models import User, UserRole, AuthResult


class AuthService:
    """
    Authentication service that handles user authentication and management.
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the authentication service.
        
        Args:
            supabase_client: Supabase client
        """
        self.supabase = supabase_client
        self.current_user = None
        self.current_session = None
    
    async def register(
        self, 
        email: str, 
        password: str, 
        full_name: str
    ) -> AuthResult:
        """
        Register a new user.
        
        Args:
            email: User's email address
            password: User's password
            full_name: User's full name
            
        Returns:
            Authentication result
        """
        # Validate inputs
        if not self._validate_email(email):
            return AuthResult(
                success=False,
                error="Invalid email format"
            )
            
        if not self._validate_password(password):
            return AuthResult(
                success=False,
                error="Password does not meet requirements"
            )
            
        if not full_name or len(full_name.strip()) < 2:
            return AuthResult(
                success=False,
                error="Full name is required (minimum 2 characters)"
            )
        
        try:
            # Register user with Supabase
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "role": UserRole.USER.value
                    }
                }
            })
            
            if auth_response.user:
                # Create user object
                user = User(
                    id=auth_response.user.id,
                    email=email,
                    full_name=full_name,
                    avatar_url=None,
                    role=UserRole.USER,
                    created_at=auth_response.user.created_at,
                    updated_at=auth_response.user.updated_at
                )
                
                # Store user in database
                self.supabase.table("users").insert({
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "avatar_url": user.avatar_url,
                    "role": user.role.value
                }).execute()
                
                # Set current user and session
                self.current_user = user
                self.current_session = auth_response.session
                
                return AuthResult(
                    success=True,
                    user=user,
                    session=auth_response.session
                )
            else:
                return AuthResult(
                    success=False,
                    error="Registration failed"
                )
                
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return AuthResult(
                success=False,
                error=str(e)
            )
    
    async def login(self, email: str, password: str) -> AuthResult:
        """
        Login a user.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Authentication result
        """
        try:
            # Login with Supabase
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                # Get user data from database
                user_response = self.supabase.table("users").select("*").eq("id", auth_response.user.id).execute()
                
                if user_response.data and len(user_response.data) > 0:
                    user_data = user_response.data[0]
                    
                    # Create user object
                    user = User(
                        id=user_data["id"],
                        email=user_data["email"],
                        full_name=user_data["full_name"],
                        avatar_url=user_data.get("avatar_url"),
                        role=UserRole(user_data["role"]),
                        created_at=auth_response.user.created_at,
                        updated_at=auth_response.user.updated_at
                    )
                    
                    # Set current user and session
                    self.current_user = user
                    self.current_session = auth_response.session
                    
                    return AuthResult(
                        success=True,
                        user=user,
                        session=auth_response.session
                    )
                else:
                    return AuthResult(
                        success=False,
                        error="User data not found"
                    )
            else:
                return AuthResult(
                    success=False,
                    error="Invalid email or password"
                )
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return AuthResult(
                success=False,
                error=str(e)
            )
    
    async def logout(self) -> bool:
        """
        Logout the current user.
        
        Returns:
            True if logout was successful, False otherwise
        """
        try:
            self.supabase.auth.sign_out()
            self.current_user = None
            self.current_session = None
            return True
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return False
    
    async def get_current_user(self) -> Optional[User]:
        """
        Get the current authenticated user.
        
        Returns:
            Current user or None if not authenticated
        """
        if self.current_user:
            return self.current_user
            
        try:
            # Get current session from Supabase
            auth_response = self.supabase.auth.get_session()
            
            if auth_response.user:
                # Get user data from database
                user_response = self.supabase.table("users").select("*").eq("id", auth_response.user.id).execute()
                
                if user_response.data and len(user_response.data) > 0:
                    user_data = user_response.data[0]
                    
                    # Create user object
                    user = User(
                        id=user_data["id"],
                        email=user_data["email"],
                        full_name=user_data["full_name"],
                        avatar_url=user_data.get("avatar_url"),
                        role=UserRole(user_data["role"]),
                        created_at=auth_response.user.created_at,
                        updated_at=auth_response.user.updated_at
                    )
                    
                    # Set current user and session
                    self.current_user = user
                    self.current_session = auth_response.session
                    
                    return user
            
            return None
                
        except Exception as e:
            logger.error(f"Get current user error: {str(e)}")
            return None
    
    async def request_password_reset(self, email: str) -> bool:
        """
        Request a password reset for the given email.
        
        Args:
            email: User's email address
            
        Returns:
            True if reset request was sent, False otherwise
        """
        try:
            self.supabase.auth.reset_password_email(email)
            return True
        except Exception as e:
            logger.error(f"Password reset request error: {str(e)}")
            return False
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset a password with the given token.
        
        Args:
            token: Reset token from email
            new_password: New password
            
        Returns:
            True if reset was successful, False otherwise
        """
        try:
            if not self._validate_password(new_password):
                return False
                
            self.supabase.auth.update_user({
                "password": new_password
            })
            return True
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            return False
    
    async def is_admin(self, user: Optional[User] = None) -> bool:
        """
        Check if the given user (or current user) is an admin.
        
        Args:
            user: User to check, or None to check current user
            
        Returns:
            True if user is an admin, False otherwise
        """
        check_user = user or await self.get_current_user()
        
        if not check_user:
            return False
            
        return check_user.role == UserRole.ADMIN
    
    async def refresh_session(self) -> bool:
        """
        Refresh the current session.
        
        Returns:
            True if session was refreshed, False otherwise
        """
        try:
            auth_response = self.supabase.auth.refresh_session()
            
            if auth_response.session:
                self.current_session = auth_response.session
                return True
                
            return False
        except Exception as e:
            logger.error(f"Session refresh error: {str(e)}")
            return False
    
    def _validate_email(self, email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            True if email is valid, False otherwise
        """
        if not email:
            return False
            
        # Simple email validation regex
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, email))
    
    def _validate_password(self, password: str) -> bool:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            True if password is valid, False otherwise
        """
        if not password or len(password) < 8:
            return False
            
        # Password must contain at least one uppercase letter
        if not any(c.isupper() for c in password):
            return False
            
        # Password must contain at least one lowercase letter
        if not any(c.islower() for c in password):
            return False
            
        # Password must contain at least one digit
        if not any(c.isdigit() for c in password):
            return False
            
        return True


def create_auth_service(supabase_client: Client) -> AuthService:
    """
    Create an authentication service.
    
    Args:
        supabase_client: Supabase client
        
    Returns:
        Authentication service
    """
    return AuthService(supabase_client)