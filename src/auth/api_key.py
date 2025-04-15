"""
API Key Management Module

This module provides API key management functionality for the application.
"""

from typing import Optional, Dict, Any, Tuple, List
import time
from datetime import datetime, timedelta

from supabase import Client
from loguru import logger

from src.security.api_security import get_api_security_manager
from src.security.error_handling import get_secure_error_handler


class APIKeyManager:
    """
    API key manager for handling API key operations.
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the API key manager.
        
        Args:
            supabase_client: Supabase client
        """
        self.supabase = supabase_client
        self.api_security = get_api_security_manager()
        self.error_handler = get_secure_error_handler()
    
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
        try:
            # Check if user exists
            user_response = self.supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not user_response.data or len(user_response.data) == 0:
                return False, None, "User not found"
            
            # Generate token with specified scopes and expiration
            expiration_seconds = expiration_days * 24 * 60 * 60
            token = self.api_security.create_token(
                subject=user_id,
                scopes=scopes,
                expiration=expiration_seconds,
                additional_claims={
                    "type": "api_key",
                    "name": name or "API Key",
                    "metadata": metadata or {}
                }
            )
            
            # Calculate expiration date
            expires_at = datetime.now() + timedelta(days=expiration_days)
            
            # Store API key information in database
            self.supabase.table("api_keys").insert({
                "user_id": user_id,
                "name": name or "API Key",
                "scopes": scopes,
                "expires_at": expires_at.isoformat(),
                "is_active": True,
                "metadata": metadata or {}
            }).execute()
            
            # Log API key generation
            self.error_handler.log_security_event(
                "api_key_generated",
                {
                    "user_id": user_id, 
                    "scopes": scopes, 
                    "expiration_days": expiration_days,
                    "name": name
                },
                severity="info"
            )
            
            return True, token, None
            
        except Exception as e:
            # Use secure error handling
            error_info = self.error_handler.handle_exception(e)
            return False, None, "Failed to generate API key"
    
    async def validate_api_key(self, api_key: str, required_scopes: Optional[List[str]] = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate an API key.
        
        Args:
            api_key: API key to validate
            required_scopes: List of required scopes
            
        Returns:
            Tuple of (is_valid, payload, error_message)
        """
        try:
            # Validate the token
            is_valid, payload, error = self.api_security.validate_token(api_key, required_scopes)
            
            if not is_valid:
                return False, None, error
                
            # Check if the token is an API key
            if payload.get("type") != "api_key":
                return False, None, "Invalid API key type"
                
            # Check if the key is still active in the database
            user_id = payload.get("sub")
            if not user_id:
                return False, None, "Invalid API key: missing user ID"
                
            # Get the API key from the database
            key_response = self.supabase.table("api_keys").select("*").eq("user_id", user_id).eq("is_active", True).execute()
            
            if not key_response.data or len(key_response.data) == 0:
                return False, None, "API key not found or inactive"
                
            return True, payload, None
            
        except Exception as e:
            # Use secure error handling
            error_info = self.error_handler.handle_exception(e)
            return False, None, "Failed to validate API key"
    
    async def revoke_api_key(self, key_id: str, user_id: str, is_admin: bool = False) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: API key ID
            user_id: User ID (for authorization check)
            is_admin: Whether the user is an admin
            
        Returns:
            True if key was revoked, False otherwise
        """
        try:
            # Check if the key exists
            key_response = self.supabase.table("api_keys").select("*").eq("id", key_id).execute()
            
            if not key_response.data or len(key_response.data) == 0:
                return False
                
            key_data = key_response.data[0]
            
            # Check if user owns this key or is an admin
            if key_data["user_id"] != user_id and not is_admin:
                # Log unauthorized revocation attempt
                self.error_handler.log_security_event(
                    "unauthorized_api_key_revocation_attempt",
                    {"key_id": key_id, "user_id": user_id},
                    severity="warning"
                )
                return False
            
            # Revoke the key
            self.supabase.table("api_keys").update({"is_active": False}).eq("id", key_id).execute()
            
            # Log API key revocation
            self.error_handler.log_security_event(
                "api_key_revoked",
                {"key_id": key_id, "user_id": user_id},
                severity="info"
            )
            
            return True
            
        except Exception as e:
            # Use secure error handling
            error_info = self.error_handler.handle_exception(e)
            return False
    
    async def list_user_api_keys(self, user_id: str, include_expired: bool = False) -> List[Dict[str, Any]]:
        """
        List API keys for a user.
        
        Args:
            user_id: User ID
            include_expired: Whether to include expired keys
            
        Returns:
            List of API keys
        """
        try:
            # Build query
            query = self.supabase.table("api_keys").select("*").eq("user_id", user_id)
            
            if not include_expired:
                # Only include active keys
                query = query.eq("is_active", True)
                
                # Only include non-expired keys
                now = datetime.now().isoformat()
                query = query.gte("expires_at", now)
            
            # Execute query
            response = query.execute()
            
            if not response.data:
                return []
                
            # Return the keys
            return response.data
            
        except Exception as e:
            # Use secure error handling
            error_info = self.error_handler.handle_exception(e)
            return []
    
    async def rotate_api_key(self, key_id: str, user_id: str, is_admin: bool = False) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Rotate an API key.
        
        Args:
            key_id: API key ID
            user_id: User ID (for authorization check)
            is_admin: Whether the user is an admin
            
        Returns:
            Tuple of (success, new_api_key, error_message)
        """
        try:
            # Check if the key exists
            key_response = self.supabase.table("api_keys").select("*").eq("id", key_id).execute()
            
            if not key_response.data or len(key_response.data) == 0:
                return False, None, "API key not found"
                
            key_data = key_response.data[0]
            
            # Check if user owns this key or is an admin
            if key_data["user_id"] != user_id and not is_admin:
                # Log unauthorized rotation attempt
                self.error_handler.log_security_event(
                    "unauthorized_api_key_rotation_attempt",
                    {"key_id": key_id, "user_id": user_id},
                    severity="warning"
                )
                return False, None, "Unauthorized"
            
            # Calculate expiration
            expires_at = datetime.fromisoformat(key_data["expires_at"].replace('Z', '+00:00'))
            now = datetime.now()
            expiration_days = max(1, (expires_at - now).days)
            
            # Generate a new API key
            success, new_key, error = await self.generate_api_key(
                user_id=key_data["user_id"],
                scopes=key_data["scopes"],
                expiration_days=expiration_days,
                name=key_data["name"],
                metadata=key_data.get("metadata", {})
            )
            
            if not success:
                return False, None, error
            
            # Revoke the old key
            self.supabase.table("api_keys").update({"is_active": False}).eq("id", key_id).execute()
            
            # Log API key rotation
            self.error_handler.log_security_event(
                "api_key_rotated",
                {"key_id": key_id, "user_id": user_id},
                severity="info"
            )
            
            return True, new_key, None
            
        except Exception as e:
            # Use secure error handling
            error_info = self.error_handler.handle_exception(e)
            return False, None, "Failed to rotate API key"


def create_api_key_manager(supabase_client: Client) -> APIKeyManager:
    """
    Create an API key manager.
    
    Args:
        supabase_client: Supabase client
        
    Returns:
        API key manager
    """
    return APIKeyManager(supabase_client)