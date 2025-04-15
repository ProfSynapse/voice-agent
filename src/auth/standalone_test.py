"""
Standalone test for the TokenRevocationStore class.
This script contains both the implementation and tests in a single file
to avoid import issues.
"""

import time

# TokenRevocationStore implementation
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
        self.revoked_tokens = {}
        
        # In-memory set of revoked user IDs
        self.revoked_users = set()
    
    def revoke_token(self, token_data):
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
    
    def revoke_all_user_tokens(self, user_id):
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
    
    def is_token_revoked(self, token_data):
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
    
    def cleanup_expired_tokens(self):
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

def get_token_revocation_store():
    """
    Get the singleton TokenRevocationStore instance.
    
    Returns:
        TokenRevocationStore instance
    """
    global _token_revocation_store
    if _token_revocation_store is None:
        _token_revocation_store = TokenRevocationStore()
    return _token_revocation_store


# Tests
def test_revoke_token():
    """Test revoking a token."""
    # Create a token revocation store
    store = TokenRevocationStore()
    
    # Create a token data
    token_data = {
        "jti": "test-jti",
        "sub": "test-user",
        "exp": time.time() + 3600  # 1 hour from now
    }
    
    # Revoke the token
    result = store.revoke_token(token_data)
    
    # Check the result
    assert result is True, "revoke_token should return True"
    
    # Check if the token is revoked
    assert store.is_token_revoked(token_data) is True, "Token should be revoked"
    print("✅ test_revoke_token passed")

def test_revoke_token_without_jti():
    """Test revoking a token without a JTI."""
    # Create a token revocation store
    store = TokenRevocationStore()
    
    # Create a token data without JTI
    token_data = {
        "sub": "test-user",
        "exp": time.time() + 3600  # 1 hour from now
    }
    
    # Revoke the token
    result = store.revoke_token(token_data)
    
    # Check the result
    assert result is False, "revoke_token should return False when no JTI is provided"
    print("✅ test_revoke_token_without_jti passed")

def test_revoke_all_user_tokens():
    """Test revoking all tokens for a user."""
    # Create a token revocation store
    store = TokenRevocationStore()
    
    # Revoke all tokens for a user
    result = store.revoke_all_user_tokens("test-user")
    
    # Check the result
    assert result is True, "revoke_all_user_tokens should return True"
    
    # Check if tokens for the user are revoked
    token_data = {
        "jti": "test-jti",
        "sub": "test-user",
        "exp": time.time() + 3600  # 1 hour from now
    }
    assert store.is_token_revoked(token_data) is True, "Token should be revoked for revoked user"
    print("✅ test_revoke_all_user_tokens passed")

def test_is_token_revoked():
    """Test checking if a token is revoked."""
    # Create a token revocation store
    store = TokenRevocationStore()
    
    # Create a token data
    token_data = {
        "jti": "test-jti",
        "sub": "test-user",
        "exp": time.time() + 3600  # 1 hour from now
    }
    
    # Check if the token is revoked (should be False)
    assert store.is_token_revoked(token_data) is False, "Token should not be revoked initially"
    
    # Revoke the token
    store.revoke_token(token_data)
    
    # Check if the token is revoked (should be True)
    assert store.is_token_revoked(token_data) is True, "Token should be revoked after calling revoke_token"
    print("✅ test_is_token_revoked passed")

def test_cleanup_expired_tokens():
    """Test cleaning up expired tokens."""
    # Create a token revocation store
    store = TokenRevocationStore()
    
    # Create an expired token data
    expired_token_data = {
        "jti": "expired-jti",
        "sub": "test-user",
        "exp": time.time() - 3600  # 1 hour ago
    }
    
    # Create a valid token data
    valid_token_data = {
        "jti": "valid-jti",
        "sub": "test-user",
        "exp": time.time() + 3600  # 1 hour from now
    }
    
    # Revoke both tokens
    store.revoke_token(expired_token_data)
    store.revoke_token(valid_token_data)
    
    # Check if both tokens are revoked
    assert store.is_token_revoked(expired_token_data) is True, "Expired token should be revoked"
    assert store.is_token_revoked(valid_token_data) is True, "Valid token should be revoked"
    
    # Clean up expired tokens
    cleaned_count = store.cleanup_expired_tokens()
    
    # Check the result
    assert cleaned_count == 1, "cleanup_expired_tokens should return 1"
    
    # Check if the expired token is no longer revoked
    assert store.is_token_revoked(expired_token_data) is False, "Expired token should not be revoked after cleanup"
    
    # Check if the valid token is still revoked
    assert store.is_token_revoked(valid_token_data) is True, "Valid token should still be revoked after cleanup"
    print("✅ test_cleanup_expired_tokens passed")

def test_get_token_revocation_store_singleton():
    """Test that get_token_revocation_store returns a singleton instance."""
    # Get the token revocation store
    store1 = get_token_revocation_store()
    store2 = get_token_revocation_store()
    
    # Check that they are the same instance
    assert store1 is store2, "get_token_revocation_store should return the same instance"
    print("✅ test_get_token_revocation_store_singleton passed")

def run_all_tests():
    """Run all tests."""
    test_revoke_token()
    test_revoke_token_without_jti()
    test_revoke_all_user_tokens()
    test_is_token_revoked()
    test_cleanup_expired_tokens()
    test_get_token_revocation_store_singleton()
    print("\n🎉 All tests passed!")

if __name__ == "__main__":
    run_all_tests()