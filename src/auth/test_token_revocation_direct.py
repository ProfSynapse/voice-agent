"""
Direct test for the TokenRevocationStore class.
This script tests the TokenRevocationStore implementation directly,
without relying on the project's test infrastructure.
"""

import time
import sys
from src.auth.token_revocation import TokenRevocationStore, get_token_revocation_store

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