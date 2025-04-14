# Authentication Module Pseudocode
# This module handles user authentication using Supabase

"""
TDD Test Cases:
- test_user_registration_success: Verify a user can register with valid credentials
- test_user_registration_invalid_email: Verify registration fails with invalid email
- test_user_registration_weak_password: Verify registration fails with weak password
- test_user_login_success: Verify a user can login with valid credentials
- test_user_login_invalid_credentials: Verify login fails with invalid credentials
- test_password_reset_request: Verify password reset email is sent
- test_password_reset_completion: Verify password can be reset with valid token
- test_session_management: Verify session is maintained and can be refreshed
- test_user_logout: Verify user can logout and session is invalidated
- test_role_verification: Verify admin role has correct permissions
"""

import os
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Define user roles
class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"

# User data structure
@dataclass
class User:
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str]
    role: UserRole
    created_at: str
    updated_at: str

# Authentication result
@dataclass
class AuthResult:
    success: bool
    user: Optional[User]
    session: Optional[Dict[str, Any]]
    error: Optional[str]

class AuthService:
    def __init__(self, supabase_client):
        """
        Initialize the authentication service with Supabase client
        
        Args:
            supabase_client: Initialized Supabase client
        """
        self.supabase = supabase_client
        self.current_user = None
        self.current_session = None
    
    def register(self, email: str, password: str, full_name: str) -> AuthResult:
        """
        Register a new user
        
        Args:
            email: User's email address
            password: User's password
            full_name: User's full name
            
        Returns:
            AuthResult with success status and user data if successful
        """
        try:
            # Validate input
            if not self._validate_email(email):
                return AuthResult(False, None, None, "Invalid email format")
            
            if not self._validate_password(password):
                return AuthResult(False, None, None, "Password does not meet requirements")
            
            # Register user with Supabase Auth
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })
            
            # Create user profile in database
            user_data = {
                "id": auth_response.user.id,
                "email": email,
                "full_name": full_name,
                "avatar_url": None,
                "role": UserRole.USER.value
            }
            
            self.supabase.table("users").insert(user_data).execute()
            
            # Create default user settings
            settings_data = {
                "user_id": auth_response.user.id,
                "theme": "light",
                "language": "en-US"
            }
            
            self.supabase.table("user_settings").insert(settings_data).execute()
            
            # Convert to User object
            user = User(
                id=auth_response.user.id,
                email=email,
                full_name=full_name,
                avatar_url=None,
                role=UserRole.USER,
                created_at=auth_response.user.created_at,
                updated_at=auth_response.user.created_at
            )
            
            return AuthResult(True, user, auth_response.session, None)
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return AuthResult(False, None, None, str(e))
    
    def login(self, email: str, password: str) -> AuthResult:
        """
        Login a user with email and password
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            AuthResult with success status and user data if successful
        """
        try:
            # Authenticate with Supabase
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Get user profile from database
            user_response = self.supabase.table("users").select("*").eq("id", auth_response.user.id).single().execute()
            
            if not user_response.data:
                return AuthResult(False, None, None, "User profile not found")
            
            # Convert to User object
            user_data = user_response.data
            user = User(
                id=user_data["id"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                avatar_url=user_data["avatar_url"],
                role=UserRole(user_data["role"]),
                created_at=user_data["created_at"],
                updated_at=user_data["updated_at"]
            )
            
            # Store current user and session
            self.current_user = user
            self.current_session = auth_response.session
            
            return AuthResult(True, user, auth_response.session, None)
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return AuthResult(False, None, None, str(e))
    
    def logout(self) -> bool:
        """
        Logout the current user
        
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
    
    def get_current_user(self) -> Optional[User]:
        """
        Get the currently logged in user
        
        Returns:
            User object if logged in, None otherwise
        """
        if self.current_user:
            return self.current_user
            
        try:
            # Check if session exists
            session = self.supabase.auth.get_session()
            
            if not session:
                return None
                
            # Get user profile from database
            user_response = self.supabase.table("users").select("*").eq("id", session.user.id).single().execute()
            
            if not user_response.data:
                return None
                
            # Convert to User object
            user_data = user_response.data
            user = User(
                id=user_data["id"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                avatar_url=user_data["avatar_url"],
                role=UserRole(user_data["role"]),
                created_at=user_data["created_at"],
                updated_at=user_data["updated_at"]
            )
            
            self.current_user = user
            self.current_session = session
            
            return user
            
        except Exception as e:
            logger.error(f"Get current user error: {str(e)}")
            return None
    
    def request_password_reset(self, email: str) -> bool:
        """
        Request a password reset for the given email
        
        Args:
            email: User's email address
            
        Returns:
            True if request was successful, False otherwise
        """
        try:
            self.supabase.auth.reset_password_for_email(email)
            return True
        except Exception as e:
            logger.error(f"Password reset request error: {str(e)}")
            return False
    
    def complete_password_reset(self, new_password: str, token: str) -> bool:
        """
        Complete a password reset with the given token
        
        Args:
            new_password: New password
            token: Reset token from email
            
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
            logger.error(f"Password reset completion error: {str(e)}")
            return False
    
    def is_admin(self, user: Optional[User] = None) -> bool:
        """
        Check if the given user (or current user) is an admin
        
        Args:
            user: User to check, or None to use current user
            
        Returns:
            True if user is admin, False otherwise
        """
        check_user = user or self.current_user
        
        if not check_user:
            return False
            
        return check_user.role == UserRole.ADMIN
    
    def refresh_session(self) -> bool:
        """
        Refresh the current session
        
        Returns:
            True if refresh was successful, False otherwise
        """
        try:
            session = self.supabase.auth.refresh_session()
            
            if session:
                self.current_session = session
                return True
            
            return False
        except Exception as e:
            logger.error(f"Session refresh error: {str(e)}")
            return False
    
    def _validate_email(self, email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email to validate
            
        Returns:
            True if email is valid, False otherwise
        """
        # Basic email validation
        return "@" in email and "." in email.split("@")[1]
    
    def _validate_password(self, password: str) -> bool:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets requirements, False otherwise
        """
        # Password must be at least 8 characters
        if len(password) < 8:
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


# Factory function to create auth service
def create_auth_service(supabase_client):
    """
    Create and initialize the authentication service
    
    Args:
        supabase_client: Initialized Supabase client
        
    Returns:
        Initialized AuthService instance
    """
    return AuthService(supabase_client)