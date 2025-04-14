"""
Token Validation Module

This module provides secure token validation for the voice agent application.
It implements token validation, expiration checks, and signed request verification.
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Dict, Any, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse

from src.security.secrets_manager import get_secrets_manager

logger = logging.getLogger(__name__)


class TokenValidator:
    """Token validator for secure API communications."""
    
    def __init__(self):
        """Initialize the token validator."""
        self.secrets = get_secrets_manager()
        
    def generate_token(
        self, 
        user_id: str, 
        scope: str = "default", 
        expiration: int = 3600,
        custom_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a secure token.
        
        Args:
            user_id: User ID
            scope: Token scope (e.g., "voice", "admin", "default")
            expiration: Token expiration time in seconds
            custom_claims: Custom claims to include in the token
            
        Returns:
            Secure token string
        """
        # Get the signing key
        signing_key = self.secrets.get("TOKEN_SIGNING_KEY")
        if not signing_key:
            # Generate a new signing key if not found
            signing_key = base64.b64encode(os.urandom(32)).decode()
            self.secrets.set("TOKEN_SIGNING_KEY", signing_key)
            
        # Create the token payload
        now = int(time.time())
        payload = {
            "sub": user_id,
            "scope": scope,
            "iat": now,
            "exp": now + expiration
        }
        
        # Add custom claims if provided
        if custom_claims:
            payload.update(custom_claims)
            
        # Encode the payload
        payload_json = json.dumps(payload)
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()
        
        # Create the signature
        signature = self._create_signature(payload_b64, signing_key)
        
        # Combine into a token
        return f"{payload_b64}.{signature}"
        
    def validate_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate a token.
        
        Args:
            token: Token to validate
            
        Returns:
            Tuple of (is_valid, payload, error_message)
        """
        if not token:
            return False, None, "Token is empty"
            
        # Split the token
        parts = token.split(".")
        if len(parts) != 2:
            return False, None, "Invalid token format"
            
        payload_b64, signature = parts
        
        # Get the signing key
        signing_key = self.secrets.get("TOKEN_SIGNING_KEY")
        if not signing_key:
            return False, None, "Signing key not found"
            
        # Verify the signature
        expected_signature = self._create_signature(payload_b64, signing_key)
        if not hmac.compare_digest(signature, expected_signature):
            return False, None, "Invalid signature"
            
        try:
            # Decode the payload
            payload_json = base64.urlsafe_b64decode(payload_b64).decode()
            payload = json.loads(payload_json)
            
            # Check expiration
            now = int(time.time())
            if payload.get("exp", 0) < now:
                return False, payload, "Token expired"
                
            return True, payload, None
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return False, None, f"Token validation error: {str(e)}"
            
    def _create_signature(self, payload: str, key: str) -> str:
        """
        Create a signature for a payload.
        
        Args:
            payload: Payload to sign
            key: Signing key
            
        Returns:
            Signature string
        """
        key_bytes = key.encode()
        payload_bytes = payload.encode()
        
        signature = hmac.new(key_bytes, payload_bytes, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(signature).decode()
        
    def verify_signed_request(self, url: str, headers: Dict[str, str], body: Optional[str] = None) -> bool:
        """
        Verify a signed request.
        
        Args:
            url: Request URL
            headers: Request headers
            body: Request body
            
        Returns:
            True if the request is valid, False otherwise
        """
        # Check if the request has the required headers
        if "X-Request-Signature" not in headers or "X-Request-Timestamp" not in headers:
            return False
            
        # Get the signature and timestamp
        signature = headers["X-Request-Signature"]
        timestamp = headers["X-Request-Timestamp"]
        
        try:
            # Check if the timestamp is recent (within 5 minutes)
            now = int(time.time())
            request_time = int(timestamp)
            if abs(now - request_time) > 300:  # 5 minutes
                logger.warning(f"Request timestamp too old: {timestamp}")
                return False
                
            # Get the signing key
            signing_key = self.secrets.get("REQUEST_SIGNING_KEY")
            if not signing_key:
                logger.error("Request signing key not found")
                return False
                
            # Create the message to verify
            parsed_url = urlparse(url)
            path = parsed_url.path
            query = parse_qs(parsed_url.query)
            
            # Sort query parameters for consistent ordering
            sorted_query = "&".join(f"{k}={v[0]}" for k, v in sorted(query.items())) if query else ""
            
            # Combine the elements to sign
            message = f"{path}"
            if sorted_query:
                message += f"?{sorted_query}"
                
            message += f"|{timestamp}"
            
            if body:
                message += f"|{body}"
                
            # Create the expected signature
            expected_signature = self._create_signature(message, signing_key)
            
            # Verify the signature
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying signed request: {str(e)}")
            return False
            
    def create_signed_request_headers(self, url: str, body: Optional[str] = None) -> Dict[str, str]:
        """
        Create headers for a signed request.
        
        Args:
            url: Request URL
            body: Request body
            
        Returns:
            Headers for the signed request
        """
        # Get the signing key
        signing_key = self.secrets.get("REQUEST_SIGNING_KEY")
        if not signing_key:
            # Generate a new signing key if not found
            signing_key = base64.b64encode(os.urandom(32)).decode()
            self.secrets.set("REQUEST_SIGNING_KEY", signing_key)
            
        # Create the timestamp
        timestamp = str(int(time.time()))
        
        # Create the message to sign
        parsed_url = urlparse(url)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)
        
        # Sort query parameters for consistent ordering
        sorted_query = "&".join(f"{k}={v[0]}" for k, v in sorted(query.items())) if query else ""
        
        # Combine the elements to sign
        message = f"{path}"
        if sorted_query:
            message += f"?{sorted_query}"
            
        message += f"|{timestamp}"
        
        if body:
            message += f"|{body}"
            
        # Create the signature
        signature = self._create_signature(message, signing_key)
        
        # Return the headers
        return {
            "X-Request-Signature": signature,
            "X-Request-Timestamp": timestamp
        }


# Create a singleton instance
_token_validator = None

def get_token_validator() -> TokenValidator:
    """
    Get the singleton TokenValidator instance.
    
    Returns:
        TokenValidator instance
    """
    global _token_validator
    if _token_validator is None:
        _token_validator = TokenValidator()
    return _token_validator