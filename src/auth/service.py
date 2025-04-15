"""
Authentication Service Module

This module provides the authentication service for the application.
"""

import logging
from typing import Optional, Dict, Any, Tuple, List

from supabase import Client
from loguru import logger

from src.auth.models import User, UserRole, AuthResult
from src.auth.security import create_auth_security_service
from src.auth.api_key import create_api_key_manager
from src.auth.jwt_auth import create_jwt_auth


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
        
        # Initialize security components
        self.security = create_auth_security_service(supabase_client)
        self.api_key_manager = create_api_key_manager(supabase_client)
        self.jwt_auth = create_jwt_auth(supabase_client)
    
    async def register(
        self, 
        email: str, 
        password: str, 
        full_name: str,
        ip_address: Optional[str] = None
    ) -> AuthResult:
        """
        Register a new user.
        
        Args:
            email: User's email address
            password: User's password
            full_name: User's full name
            ip_address: IP address of the request (for rate limiting)
            
        Returns:
            Authentication result
        """
        try:
            # Apply rate limiting for registration attempts
            is_allowed, limit_info = self.security.validate_registration_attempt(ip_address)
            if not is_allowed:
                return AuthResult(
                    success=False,
                    error="Too many registration attempts. Please try again later."
                )
            
            # Validate inputs using the enhanced validator
            is_valid, error_msg = self.security.validate_email(email)
            if not is_valid:
                return AuthResult(success=False, error=error_msg)
                
            is_valid, error_msg = self.security.validate_password(password, email)
            if not is_valid:
                return AuthResult(success=False, error=error_msg)
                
            is_valid, error_msg = self.security.validate_text(
                full_name, 
                min_length=2, 
                max_length=100
            )
            if not is_valid:
                return AuthResult(success=False, error=error_msg)
            
            # Register user with Supabase
            auth_response = await self.supabase.auth.sign_up({
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
                # Increment rate limit counter after successful registration
                self.security.increment_auth_attempt(ip_address)
                
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
                
                # Log successful registration
                self.security.log_security_event(
                    "user_registered",
                    {"user_id": user.id},
                    severity="info"
                )
                
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
            # Use secure error handling
            error_info = self.security.handle_exception(
                e, 
                context={"email": self.security.redact_sensitive_data(email)}
            )
            
            return AuthResult(
                success=False,
                error="An error occurred during registration. Please try again."
            )
    
    async def login(
        self, 
        email: str, 
        password: str,
        ip_address: Optional[str] = None
    ) -> AuthResult:
        """
        Login a user.
        
        Args:
            email: User's email address
            password: User's password
            ip_address: IP address of the request (for rate limiting)
            
        Returns:
            Authentication result
        """
        try:
            # Apply rate limiting for login attempts
            is_allowed, limit_info = self.security.validate_login_attempt(ip_address)
            if not is_allowed:
                return AuthResult(
                    success=False,
                    error="Too many login attempts. Please try again later."
                )
            
            # Login with Supabase
            auth_response = await self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                # Reset rate limiter for this IP after successful login
                self.security.reset_auth_attempts(ip_address)
                
                # Get user data from database
                user_response = await self.supabase.table("users").select("*").eq("id", auth_response.user.id).execute()
                
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
                    
                    # Log successful login
                    self.security.log_security_event(
                        "user_login",
                        {"user_id": user.id},
                        severity="info"
                    )
                    
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
                # Increment failed login counter
                self.security.increment_auth_attempt(ip_address)
                
                # Log failed login attempt
                self.security.log_security_event(
                    "failed_login",
                    {"email": self.security.redact_sensitive_data(email), "ip": ip_address},
                    severity="warning"
                )
                
                return AuthResult(
                    success=False,
                    error="Invalid email or password"
                )
                
        except Exception as e:
            # Use secure error handling
            error_info = self.security.handle_exception(
                e, 
                context={"email": self.security.redact_sensitive_data(email)}
            )
            
            return AuthResult(
                success=False,
                error="An error occurred during login. Please try again."
            )
    
    async def logout(self) -> bool:
        """
        Logout the current user.
        
        Returns:
            True if logout was successful, False otherwise
        """
        try:
            user_id = self.current_user.id if self.current_user else None
            
            # Revoke the current session token if available
            if self.current_session and hasattr(self.current_session, "access_token"):
                try:
                    self.jwt_auth.revoke_token_by_token(self.current_session.access_token)
                    logger.info(f"Revoked access token for user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to revoke token during logout: {str(e)}")
            
            await self.supabase.auth.sign_out()
            self.current_user = None
            self.current_session = None
            
            # Log successful logout
            if user_id:
                self.security.log_security_event(
                    "user_logout",
                    {"user_id": user_id},
                    severity="info"
                )
                
            return True
        except Exception as e:
            # Use secure error handling
            error_info = self.security.handle_exception(e)
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
            auth_response = await self.supabase.auth.get_session()
            
            if auth_response.user:
                # Validate the session token
                session_token = auth_response.session.access_token if auth_response.session else None
                
                if session_token:
                    # Get user data from database
                    user_response = await self.supabase.table("users").select("*").eq("id", auth_response.user.id).execute()
                    
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
            # Use secure error handling
            error_info = self.security.handle_exception(e)
            return None
    
    async def request_password_reset(self, email: str, ip_address: Optional[str] = None) -> bool:
        """
        Request a password reset for the given email.
        
        Args:
            email: User's email address
            ip_address: IP address of the request (for rate limiting)
            
        Returns:
            True if reset request was sent, False otherwise
        """
        try:
            # Apply rate limiting for password reset attempts
            is_allowed, limit_info = self.security.validate_password_reset_attempt(ip_address)
            if not is_allowed:
                return False
            
            # Validate email
            is_valid, error_msg = self.security.validate_email(email)
            if not is_valid:
                return False
            
            # Increment rate limit counter
            self.security.increment_auth_attempt(ip_address)
            
            await self.supabase.auth.reset_password_email(email)
            
            # Log password reset request
            self.security.log_security_event(
                "password_reset_requested",
                {"email": self.security.redact_sensitive_data(email)},
                severity="info"
            )
            
            return True
        except Exception as e:
            # Use secure error handling
            error_info = self.security.handle_exception(
                e, 
                context={"email": self.security.redact_sensitive_data(email)}
            )
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
            # Validate token
            is_valid, payload, error = self.security.validate_session_token(token)
            if not is_valid:
                self.security.log_security_event(
                    "invalid_password_reset_token",
                    {"error": error},
                    severity="warning"
                )
                return False
            
            # Validate password
            is_valid, error_msg = self.security.validate_password(new_password)
            if not is_valid:
                return False
                
            await self.supabase.auth.update_user({
                "password": new_password
            })
            
            # Log successful password reset
            if payload and "sub" in payload:
                self.security.log_security_event(
                    "password_reset_successful",
                    {"user_id": payload["sub"]},
                    severity="info"
                )
            
            return True
        except Exception as e:
            # Use secure error handling
            error_info = self.security.handle_exception(e)
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
            # First try to refresh using Supabase's built-in refresh
            auth_response = await self.supabase.auth.refresh_session()
            
            if auth_response.session:
                self.current_session = auth_response.session
                
                # Log session refresh
                if self.current_user:
                    self.security.log_security_event(
                        "session_refreshed",
                        {"user_id": self.current_user.id},
                        severity="info"
                    )
                
                return True
            
            # If Supabase refresh fails but we have a current session with a refresh token,
            # try to use our custom JWT refresh mechanism
            elif self.current_session and hasattr(self.current_session, "refresh_token"):
                try:
                    # Use our JWT auth to refresh the tokens
                    access_token, refresh_token = self.jwt_auth.refresh_token(
                        self.current_session.refresh_token
                    )
                    
                    # Update the session with new tokens
                    # Note: This is a simplified approach - in a real implementation,
                    # you would need to properly update the Supabase session object
                    self.current_session.access_token = access_token
                    self.current_session.refresh_token = refresh_token
                    
                    # Log session refresh
                    if self.current_user:
                        self.security.log_security_event(
                            "session_refreshed_custom",
                            {"user_id": self.current_user.id},
                            severity="info"
                        )
                    
                    return True
                except Exception as e:
                    logger.warning(f"Custom token refresh failed: {str(e)}")
                    return False
                
            return False
        except Exception as e:
            # Use secure error handling
            error_info = self.security.handle_exception(e)
            return False
            
    async def revoke_session(self, session_token: str) -> bool:
        """
        Revoke a session token.
        
        Args:
            session_token: Session token to revoke
            
        Returns:
            True if session was revoked, False otherwise
        """
        try:
            # Revoke the token
            self.jwt_auth.revoke_token_by_token(session_token)
            
            # Log session revocation
            if self.current_user:
                self.security.log_security_event(
                    "session_revoked",
                    {"user_id": self.current_user.id},
                    severity="info"
                )
            
            return True
        except Exception as e:
            # Use secure error handling
            error_info = self.security.handle_exception(e)
            return False
    
    # API Key Management Methods
    
    async def generate_api_key(
        self, 
        user_id: str, 
        scopes: List[str], 
        expiration_days: int = 30,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate an API key for a user.
        
        Args:
            user_id: User ID
            scopes: List of permission scopes
            expiration_days: Number of days until the key expires
            name: Optional name for the API key
            metadata: Optional metadata for the API key
            
        Returns:
            Tuple of (success, api_key, error_message)
        """
        return await self.api_key_manager.generate_api_key(
            user_id, 
            scopes, 
            expiration_days,
            name,
            metadata
        )
    
    async def validate_api_key(
        self, 
        api_key: str, 
        required_scopes: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate an API key.
        
        Args:
            api_key: API key to validate
            required_scopes: List of required scopes
            
        Returns:
            Tuple of (is_valid, payload, error_message)
        """
        return await self.api_key_manager.validate_api_key(api_key, required_scopes)
    
    async def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: API key ID
            user_id: User ID (for authorization check)
            
        Returns:
            True if key was revoked, False otherwise
        """
        is_admin = await self.is_admin()
        return await self.api_key_manager.revoke_api_key(key_id, user_id, is_admin)
    
    async def list_user_api_keys(
        self, 
        user_id: str, 
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List API keys for a user.
        
        Args:
            user_id: User ID
            include_expired: Whether to include expired keys
            
        Returns:
            List of API keys
        """
        return await self.api_key_manager.list_user_api_keys(user_id, include_expired)
    
    async def rotate_api_key(self, key_id: str, user_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Rotate an API key.
        
        Args:
            key_id: API key ID
            user_id: User ID (for authorization check)
            
        Returns:
            Tuple of (success, new_api_key, error_message)
        """
        is_admin = await self.is_admin()
        return await self.api_key_manager.rotate_api_key(key_id, user_id, is_admin)

def create_auth_service(supabase_client: Client) -> AuthService:
    """
    Create an authentication service.
    
    Args:
        supabase_client: Supabase client
        
    Returns:
        Authentication service
    """
    return AuthService(supabase_client)


# Global instance for dependency injection
_auth_service = None


def get_auth_service() -> AuthService:
    """
    Get the global auth service instance.
    
    Returns:
        AuthService instance
    """
    global _auth_service
    if _auth_service is None:
        from src.utils.supabase_client import get_supabase_client
        _auth_service = create_auth_service(get_supabase_client())
    return _auth_service


async def get_current_user():
    """
    FastAPI dependency to get the current authenticated user.
    
    Returns:
        Current user
    
    Raises:
        HTTPException: If user is not authenticated
    """
    from fastapi import HTTPException, status
    
    auth_service = get_auth_service()
    user = await auth_service.get_current_user()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user
    return AuthService(supabase_client)