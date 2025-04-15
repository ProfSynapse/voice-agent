"""
JWT Token Revocation Module

This module provides functionality for revoking JWT tokens, including:
- Token revocation storage
- Token validation with revocation check
- Automatic cleanup of expired tokens
"""

import time
from typing import Dict, Any, Set


class TokenRevocationStore:
    """
    Token revocation store for managing revoked JWT tokens.
    
    This class provides functionality to:
    1. Revoke tokens by storing their JTI (JWT ID)
    2. Revoke all tokens for a specific user
    3. Check if a token is revoked
    4. Clean up expired tokens
    """
    
    def __init__(self):
        """Initialize the token revocation store."""
        # In-memory store of revoked tokens (jti -> expiration timestamp)
        self.revoked_tokens: Dict[str, float] = {}
        
        # In-memory set of revoked user IDs
        self.revoked_users: Set[str] = set()
    
    def revoke_token(self, token_data: Dict[str, Any]) -> bool:
        """
        Revoke a JWT token.
        
        Args:
            token_data: Token data containing jti, sub, and exp
            
        Returns:
            True if token was revoked, False otherwise
        """
        # Extract token data
        jti = token_data.get("jti")
        exp = token_data.get("exp")
        
        if not jti:
            return False
            
        # Store in memory
        self.revoked_tokens[jti] = exp if exp else time.time() + 86400  # Default 24h expiry
        return True
    
    def revoke_all_user_tokens(self, user_id: str) -> bool:
        """
        Revoke all tokens for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if user tokens were revoked, False otherwise
        """
        # Add to revoked users set
        self.revoked_users.add(user_id)
        return True
    
    def is_token_revoked(self, token_data: Dict[str, Any]) -> bool:
        """
        Check if a token is revoked.
        
        Args:
            token_data: Token data containing jti and sub (user_id)
            
        Returns:
            True if token is revoked, False otherwise
        """
        # Extract token data
        jti = token_data.get("jti")
        user_id = token_data.get("sub")
        
        # Check if user is revoked
        if user_id and user_id in self.revoked_users:
            return True
            
        # Check if token is revoked
        if jti and jti in self.revoked_tokens:
            # Even if the token has expired, we still consider it revoked
            # until cleanup_expired_tokens is explicitly called
            return True
            
        return False
    
    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens from memory.
        
        Returns:
            Number of tokens cleaned up
        """
        now = time.time()
        expired_tokens = [jti for jti, exp in self.revoked_tokens.items() if exp < now]
        
        for jti in expired_tokens:
            del self.revoked_tokens[jti]
            
        return len(expired_tokens)


# Singleton instance
_token_revocation_store = None

def get_token_revocation_store() -> TokenRevocationStore:
    """
    Get the singleton TokenRevocationStore instance.
    
    Returns:
        TokenRevocationStore instance
    """
    global _token_revocation_store
    if _token_revocation_store is None:
        _token_revocation_store = TokenRevocationStore()
    return _token_revocation_store