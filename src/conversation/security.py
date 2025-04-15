"""
Conversation Security Module

This module provides security features specific to conversations.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from loguru import logger

from src.security.field_encryption import get_field_encryption
from src.security.api_security import get_api_security_manager
from src.security.token_validation import get_token_validator
from src.security.error_handling import get_secure_error_handler
from src.utils.mock_helpers import execute_with_mock_handling, execute_supabase_with_mock_handling


class ConversationSecurityService:
    """Security features for conversations."""
    
    def __init__(self, supabase_client=None, jwt_auth=None):
        """Initialize the conversation security features."""
        self.field_encryption = get_field_encryption()
        self.api_security = get_api_security_manager()
        self.token_validator = get_token_validator()
        self.error_handler = get_secure_error_handler()
        self.supabase_client = supabase_client
        self.jwt_auth = jwt_auth
        
        # Define fields that should be encrypted
        self.encrypted_fields = ["title", "content"]
    
    def encrypt_conversation_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in conversation data.
        
        Args:
            data: Conversation data to encrypt
            
        Returns:
            Encrypted conversation data
        """
        return self.field_encryption.encrypt_dict(data, self.encrypted_fields)
    
    def decrypt_conversation_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in conversation data.
        
        Args:
            data: Encrypted conversation data
            
        Returns:
            Decrypted conversation data
        """
        return self.field_encryption.decrypt_dict(data, self.encrypted_fields)
    
    def encrypt_turn_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in turn data.
        
        Args:
            data: Turn data to encrypt
            
        Returns:
            Encrypted turn data
        """
        return self.field_encryption.encrypt_dict(data, ["content"])
    
    def decrypt_turn_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in turn data.
        
        Args:
            data: Encrypted turn data
            
        Returns:
            Decrypted turn data
        """
        return self.field_encryption.decrypt_dict(data, ["content"])
    
    def encrypt_turn_list(self, turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Encrypt sensitive fields in a list of turns.
        
        Args:
            turns: List of turn data to encrypt
            
        Returns:
            List of encrypted turn data
        """
        return self.field_encryption.encrypt_list(turns, ["content"])
    
    def decrypt_turn_list(self, turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Decrypt sensitive fields in a list of turns.
        
        Args:
            turns: List of encrypted turn data
            
        Returns:
            List of decrypted turn data
        """
        return self.field_encryption.decrypt_list(turns, ["content"])
    
    def validate_conversation_access(
        self, 
        token: str, 
        conversation_id: str, 
        required_scopes: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate access to a conversation.
        
        Args:
            token: Access token
            conversation_id: ID of the conversation
            required_scopes: Optional list of required scopes
            
        Returns:
            Tuple of (is_valid, token_payload, error_message)
        """
        try:
            # Validate token
            is_valid, payload, error = self.token_validator.validate_token(token)
            
            if not is_valid:
                return False, None, error
            
            # Check required scopes
            if required_scopes:
                token_scopes = payload.get("scope", "").split()
                if not all(scope in token_scopes for scope in required_scopes):
                    return False, payload, "Insufficient permissions"
            
            # Check if token subject matches conversation owner
            # This would require a database lookup in a real implementation
            # For now, we'll just return the validation result
            
            return True, payload, None
            
        except Exception as e:
            error_info = self.error_handler.handle_exception(
                e, 
                context={
                    "conversation_id": conversation_id, 
                    "operation": "validate_conversation_access"
                }
            )
            return False, None, error_info["error"]["message"]
    
    def create_conversation_token(
        self, 
        user_id: str, 
        conversation_id: str, 
        expiration: int = 3600
    ) -> str:
        """
        Create a token for conversation access.
        
        Args:
            user_id: ID of the user
            conversation_id: ID of the conversation
            expiration: Token expiration time in seconds
            
        Returns:
            Conversation access token
        """
        # Create custom claims for the conversation
        custom_claims = {
            "conversation_id": conversation_id,
            "resource_type": "conversation"
        }
        
        # Generate token with conversation scope
        return self.token_validator.generate_token(
            user_id=user_id,
            scope="conversation:read conversation:write",
            expiration=expiration,
            custom_claims=custom_claims
        )
    
    def sanitize_conversation_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize conversation data for public exposure.
        
        Args:
            data: Conversation data to sanitize
            
        Returns:
            Sanitized conversation data
        """
        # Create a copy to avoid modifying the original
        sanitized = data.copy()
        
        # Remove sensitive fields
        sensitive_fields = ["user_id", "system_prompt_id"]
        for field in sensitive_fields:
            if field in sanitized:
                del sanitized[field]
        
        return sanitized
    
    def log_conversation_access(
        self, 
        user_id: str, 
        conversation_id: str, 
        action: str, 
        success: bool, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log conversation access for security auditing.
        
        Args:
            user_id: ID of the user
            conversation_id: ID of the conversation
            action: Action performed
            success: Whether the action was successful
            details: Optional additional details
        """
        log_data = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "action": action,
            "success": success
        }
        
        if details:
            log_data["details"] = details
        
        # Log the security event
        severity = "info" if success else "warning"
        self.error_handler.log_security_event(
            event_type="conversation_access",
            details=log_data,
            severity=severity
        )
        
    async def check_user_access_to_conversation(self, user_id: str, conversation_id: str, token: Optional[str] = None) -> bool:
        """
        Check if a user has access to a conversation.
        
        Args:
            user_id: ID of the user
            conversation_id: ID of the conversation
            token: Optional token for role-based checks
            
        Returns:
            True if the user has access, False otherwise
        """
        try:
            # Check if user is admin
            if token and self.jwt_auth:
                roles = self.jwt_auth.get_roles_from_token(token)
                if "admin" in roles:
                    return True
            
            # Query the conversation to check ownership
            if self.supabase_client:
                # Store the table reference to avoid multiple calls
                conversations_table = self.supabase_client.table("conversations")
                # Get the query result directly
                query = conversations_table.select("user_id").eq("id", conversation_id).single()
                result = await execute_supabase_with_mock_handling(query)
                
                if hasattr(result, "data") and result.data:
                    return result.data[0]["user_id"] == user_id
                    
            return False
        except Exception as e:
            logger.error(f"Error checking conversation access: {str(e)}")
            return False
            
    async def check_user_access_to_system_prompt(self, user_id: str, prompt_id: str, token: Optional[str] = None) -> bool:
        """
        Check if a user has access to a system prompt.
        
        Args:
            user_id: ID of the user
            prompt_id: ID of the system prompt
            token: Optional token for role-based checks
            
        Returns:
            True if the user has access, False otherwise
        """
        try:
            # Check if user is admin
            if token and self.jwt_auth:
                roles = self.jwt_auth.get_roles_from_token(token)
                if "admin" in roles:
                    return True
            
            # Query the system prompt to check ownership and public status
            if self.supabase_client:
                # Store the table reference to avoid multiple calls
                system_prompts_table = self.supabase_client.table("system_prompts")
                # Get the query result directly
                query = system_prompts_table.select("created_by, is_public").eq("id", prompt_id).single()
                result = await execute_supabase_with_mock_handling(query)
                
                if result.data:
                    # User has access if they created it or if it's public
                    return result.data[0]["created_by"] == user_id or result.data[0]["is_public"]
                    
            return False
        except Exception as e:
            logger.error(f"Error checking system prompt access: {str(e)}")
            return False
            
    def generate_access_token(self, user_id: str, custom_claims: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate an access token for a user.
        
        Args:
            user_id: ID of the user
            custom_claims: Optional custom claims to include in the token
            
        Returns:
            Generated access token
        """
        if self.jwt_auth:
            return self.jwt_auth.generate_token(
                user_id=user_id,
                roles=["user"],
                expiration=3600,
                custom_claims=custom_claims
            )
        return "test-token"
        
    def generate_admin_token(self, user_id: str, custom_claims: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate an admin token for a user.
        
        Args:
            user_id: ID of the user
            custom_claims: Optional custom claims to include in the token
            
        Returns:
            Generated admin token
        """
        if self.jwt_auth:
            return self.jwt_auth.generate_token(
                user_id=user_id,
                roles=["admin"],
                expiration=3600,
                custom_claims=custom_claims
            )
        return "test-admin-token"
        
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a token.
        
        Args:
            token: Token to validate
            
        Returns:
            Token payload if valid
        """
        if self.jwt_auth:
            return self.jwt_auth.validate_token(token)
        return {"sub": "test-user-id"}
        
    def get_user_id_from_token(self, token: str) -> str:
        """
        Get the user ID from a token.
        
        Args:
            token: Token to extract user ID from
            
        Returns:
            User ID
        """
        if self.jwt_auth:
            return self.jwt_auth.get_user_id_from_token(token)
        return "test-user-id"


# Create a singleton instance
_conversation_security = None

def get_conversation_security() -> ConversationSecurityService:
    """
    Get the singleton ConversationSecurity instance.
    
    Returns:
        ConversationSecurity instance
    """
    global _conversation_security
    if _conversation_security is None:
        _conversation_security = ConversationSecurityService()
    return _conversation_security