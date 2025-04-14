"""
API Security Module

This module provides security features for API communications, including:
- Secure API key management with key rotation
- Token validation with expiration checks
- Principle of least privilege for token generation
- Signed request implementation
"""

import os
import time
import hmac
import hashlib
import base64
import json
import secrets
import logging
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qsl, urlencode

import jwt
from loguru import logger

from src.security.secrets_manager import get_secrets_manager


class TokenExpiredError(Exception):
    """Exception raised when a token has expired."""
    pass


class TokenInvalidError(Exception):
    """Exception raised when a token is invalid."""
    pass


class APISecurityManager:
    """
    API Security Manager for handling secure API communications.
    
    This class provides:
    1. Secure API key management with key rotation
    2. Token validation with expiration checks
    3. Principle of least privilege for token generation
    4. Signed request implementation
    """
    
    def __init__(self):
        """Initialize the API security manager."""
        self.secrets = get_secrets_manager()
        
    def create_token(
        self, 
        subject: str, 
        scopes: List[str], 
        expiration: int = 3600,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a JWT token with the principle of least privilege.
        
        Args:
            subject: Subject of the token (usually user ID)
            scopes: List of permission scopes to include
            expiration: Token expiration time in seconds
            additional_claims: Additional claims to include in the token
            
        Returns:
            JWT token string
        """
        # Get the secret key
        secret_key = self.secrets.get("APP_SECRET_KEY", required=True)
        
        # Create token payload
        now = int(time.time())
        payload = {
            "sub": subject,
            "scopes": scopes,
            "iat": now,
            "exp": now + expiration,
            "jti": secrets.token_hex(16)  # Unique token ID to prevent replay attacks
        }
        
        # Add additional claims
        if additional_claims:
            payload.update(additional_claims)
            
        # Create and sign the token
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        return token
        
    def validate_token(
        self, 
        token: str, 
        required_scopes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate a JWT token and check required scopes.
        
        Args:
            token: JWT token to validate
            required_scopes: List of required scopes
            
        Returns:
            Token payload if valid
            
        Raises:
            TokenExpiredError: If the token has expired
            TokenInvalidError: If the token is invalid or missing required scopes
        """
        # Get the secret key
        secret_key = self.secrets.get("APP_SECRET_KEY", required=True)
        
        try:
            # Decode and verify the token
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            
            # Check if token has expired
            now = int(time.time())
            if payload.get("exp", 0) < now:
                raise TokenExpiredError("Token has expired")
                
            # Check required scopes
            if required_scopes:
                token_scopes = payload.get("scopes", [])
                if not all(scope in token_scopes for scope in required_scopes):
                    raise TokenInvalidError("Token missing required scopes")
                    
            return payload
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid token: {str(e)}")
            
    def create_livekit_token(
        self, 
        room_name: str, 
        participant_name: str,
        ttl: int = 3600,
        can_publish: bool = True,
        can_subscribe: bool = True
    ) -> str:
        """
        Create a LiveKit token with the principle of least privilege.
        
        Args:
            room_name: Name of the LiveKit room
            participant_name: Name of the participant
            ttl: Token time-to-live in seconds
            can_publish: Whether the participant can publish
            can_subscribe: Whether the participant can subscribe
            
        Returns:
            LiveKit token string
        """
        from livekit import AccessToken
        
        # Get LiveKit credentials
        api_key = self.secrets.get("LIVEKIT_API_KEY", required=True)
        api_secret = self.secrets.get("LIVEKIT_API_SECRET", required=True)
        
        # Create token with minimal permissions
        token = AccessToken(api_key=api_key, api_secret=api_secret)
        
        # Set token identity and metadata
        token.identity = participant_name
        token.name = participant_name
        
        # Set token expiration
        token.ttl = ttl
        
        # Add room permissions with principle of least privilege
        token.add_grant(
            room=room_name,
            room_join=True,
            room_publish=can_publish,
            room_subscribe=can_subscribe,
            can_publish=can_publish,
            can_subscribe=can_subscribe
        )
        
        return token.to_jwt()
        
    def sign_request(
        self, 
        method: str, 
        url: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Create signed request headers for API communication.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            data: Request data
            headers: Existing headers
            
        Returns:
            Headers dictionary with signature
        """
        # Get API credentials
        api_key = self.secrets.get("API_KEY", required=True)
        api_secret = self.secrets.get("API_SECRET", required=True)
        
        # Initialize headers
        if headers is None:
            headers = {}
            
        # Add timestamp
        timestamp = str(int(time.time()))
        headers["X-Timestamp"] = timestamp
        
        # Add API key
        headers["X-Api-Key"] = api_key
        
        # Create signature base string
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # Create string to sign
        components = [method.upper(), path, timestamp]
        
        # Add query parameters if present
        if parsed_url.query:
            query_params = dict(parse_qsl(parsed_url.query))
            sorted_query = "&".join(f"{k}={query_params[k]}" for k in sorted(query_params.keys()))
            components.append(sorted_query)
            
        # Add body data if present
        if data:
            body_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
            components.append(body_str)
            
        string_to_sign = "\n".join(components)
        
        # Create signature
        signature = hmac.new(
            api_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256
        ).digest()
        
        # Add signature to headers
        headers["X-Signature"] = base64.b64encode(signature).decode("utf-8")
        
        return headers
        
    def verify_signature(
        self, 
        method: str, 
        url: str, 
        headers: Dict[str, str],
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Verify a request signature.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            data: Request data
            
        Returns:
            True if signature is valid, False otherwise
        """
        # Get required headers
        api_key = headers.get("X-Api-Key")
        timestamp = headers.get("X-Timestamp")
        signature = headers.get("X-Signature")
        
        if not all([api_key, timestamp, signature]):
            return False
            
        # Check timestamp to prevent replay attacks
        try:
            request_time = int(timestamp)
            now = int(time.time())
            if abs(now - request_time) > 300:  # 5 minutes
                return False
        except ValueError:
            return False
            
        # Get API secret for the provided key
        api_secret = self.secrets.get("API_SECRET", required=True)
        
        # Create signature base string (same as in sign_request)
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # Create string to sign
        components = [method.upper(), path, timestamp]
        
        # Add query parameters if present
        if parsed_url.query:
            query_params = dict(parse_qsl(parsed_url.query))
            sorted_query = "&".join(f"{k}={query_params[k]}" for k in sorted(query_params.keys()))
            components.append(sorted_query)
            
        # Add body data if present
        if data:
            body_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
            components.append(body_str)
            
        string_to_sign = "\n".join(components)
        
        # Create expected signature
        expected_signature = hmac.new(
            api_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256
        ).digest()
        
        expected_signature_b64 = base64.b64encode(expected_signature).decode("utf-8")
        
        # Compare signatures using constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature_b64)


# Create a singleton instance
_api_security_manager = None

def get_api_security_manager() -> APISecurityManager:
    """
    Get the singleton APISecurityManager instance.
    
    Returns:
        APISecurityManager instance
    """
    global _api_security_manager
    if _api_security_manager is None:
        _api_security_manager = APISecurityManager()
    return _api_security_manager