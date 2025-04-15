"""
Secrets Manager Module

This module provides secure secrets management for the voice agent application.
It implements secure storage, retrieval, and encryption of sensitive configuration values.
"""

import os
import json
from loguru import logger
import base64
from typing import Dict, Any, Optional, Union, Tuple
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Import inside methods to avoid circular imports


class SecretsManager:
    """Secure secrets manager for handling sensitive configuration values."""
    
    def __init__(self, app_name: str = "voice_agent", master_key: Optional[str] = None):
        """
        Initialize the secrets manager.
        
        Args:
            app_name: Application name for namespacing secrets
            master_key: Optional master key for encryption (if None, will try to get from environment)
        """
        self.app_name = app_name
        self.secrets_cache: Dict[str, Any] = {}
        self._master_key = master_key
        self.encryption_key = self._get_encryption_key()
        self._load_secrets()
        
    def _get_encryption_key(self) -> bytes:
        """
        Get the encryption key from the master key.
        
        Returns:
            Encryption key bytes
            
        Raises:
            RuntimeError: If no master key is available
        """
        # Get the master key from environment or use the provided one
        if self._master_key is None:
            # Try to get from environment directly to avoid circular dependency
            self._master_key = os.environ.get("SECRETS_MASTER_KEY", "default-dev-key-not-for-production")
        
        master_key = self._master_key
        
        # Check if we're in production mode directly from environment
        is_production = os.environ.get("APP_ENV") == "production"
        
        if not master_key:
            error_msg = "SECRETS_MASTER_KEY not found in environment. This is required for secure operation."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Validate the master key
        if len(master_key) < 16:
            error_msg = "SECRETS_MASTER_KEY is too short. It should be at least 16 characters."
            logger.error(error_msg)
            if is_production:
                raise RuntimeError(error_msg)
            else:
                logger.warning("Continuing with insecure master key in development mode.")
        
        # Derive a key using PBKDF2
        salt = self.app_name.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        return key
        
    def _get_secrets_path(self) -> Path:
        """
        Get the path to the secrets file.
        
        Returns:
            Path to the secrets file
        """
        # In production, use a more secure location
        base_dir = Path(os.environ.get("SECRETS_DIR", Path.home() / ".config" / self.app_name))
        base_dir.mkdir(parents=True, exist_ok=True)
        
        return base_dir / "secrets.enc"
        
    def _load_secrets(self) -> None:
        """Load secrets from the encrypted secrets file."""
        secrets_path = self._get_secrets_path()
        
        if not secrets_path.exists():
            logger.info(f"Secrets file not found at {secrets_path}. Creating a new one.")
            self.secrets_cache = {}
            self._save_secrets()
            return
            
        try:
            with open(secrets_path, "rb") as f:
                encrypted_data = f.read()
                
            if not encrypted_data:
                self.secrets_cache = {}
                return
                
            fernet = Fernet(self.encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data)
            self.secrets_cache = json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Error loading secrets: {str(e)}")
            self.secrets_cache = {}
            
    def _save_secrets(self) -> None:
        """Save secrets to the encrypted secrets file."""
        secrets_path = self._get_secrets_path()
        
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(json.dumps(self.secrets_cache).encode())
            
            with open(secrets_path, "wb") as f:
                f.write(encrypted_data)
                
            # Set secure permissions on the file
            os.chmod(secrets_path, 0o600)  # Only owner can read/write
        except Exception as e:
            logger.error(f"Error saving secrets: {str(e)}")
    
    def get(self, key: str, default: Any = None, required: bool = False) -> Any:
        """
        Get a secret value.
        
        Args:
            key: Secret key
            default: Default value if key not found
            required: Whether the secret is required
            
        Returns:
            Secret value or default
            
        Raises:
            ValueError: If the secret is required but not found
        """
        # First check environment variables (highest priority)
        env_value = os.environ.get(key)
        if env_value is not None:
            # Validate the environment variable
            self._validate_secret(key, env_value)
            return env_value
            
        # Then check the secrets cache
        cached_value = self.secrets_cache.get(key)
        if cached_value is not None:
            return cached_value
            
        # Check if the secret is required
        if required:
            error_msg = f"Required secret {key} not found"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Finally, return the default
        if default is not None:
            logger.warning(f"Secret {key} not found, using default value")
        else:
            logger.warning(f"Secret {key} not found and no default provided")
            
        return default
        
    def set(self, key: str, value: Any) -> None:
        """
        Set a secret value.
        
        Args:
            key: Secret key
            value: Secret value
        """
        # Validate the secret value
        self._validate_secret(key, value)
        
        # Store in cache
        self.secrets_cache[key] = value
        self._save_secrets()
        
    def delete(self, key: str) -> bool:
        """
        Delete a secret.
        
        Args:
            key: Secret key
            
        Returns:
            True if deleted, False if not found
        """
        if key in self.secrets_cache:
            del self.secrets_cache[key]
            self._save_secrets()
            return True
        return False
        
    def encrypt_value(self, value: str) -> str:
        """
        Encrypt a value.
        
        Args:
            value: Value to encrypt
            
        Returns:
            Encrypted value as a string
        """
        fernet = Fernet(self.encryption_key)
        encrypted = fernet.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
        
    def decrypt_value(self, encrypted_value: str) -> str:
        """
        Decrypt a value.
        
        Args:
            encrypted_value: Encrypted value as a string
            
        Returns:
            Decrypted value
        """
        try:
            fernet = Fernet(self.encryption_key)
            decrypted = fernet.decrypt(base64.urlsafe_b64decode(encrypted_value))
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting value: {str(e)}")
            return None
            
    def _validate_secret(self, key: str, value: Any) -> None:
        """
        Validate a secret value.
        
        Args:
            key: Secret key
            value: Secret value to validate
            
        Raises:
            ValueError: If the secret value is invalid
        """
        # Skip validation for empty values
        if value is None or (isinstance(value, str) and not value.strip()):
            return
            
        # Validate based on key patterns
        if key.endswith("_KEY") or key.endswith("_SECRET") or key.endswith("_TOKEN"):
            # API keys, secrets, and tokens should have minimum length
            if isinstance(value, str) and len(value) < 8:
                logger.warning(f"Secret {key} is suspiciously short ({len(value)} chars)")
                
        elif key.endswith("_PASSWORD"):
            # Passwords should have some complexity
            if isinstance(value, str) and (len(value) < 8 or value.isalpha() or value.isdigit()):
                logger.warning(f"Secret {key} appears to be a weak password")
                
        # Check for obviously invalid values
        if isinstance(value, str):
            invalid_values = ["changeme", "default", "password", "secret", "apikey", "test", "example"]
            if value.lower() in invalid_values or any(v in value.lower() for v in invalid_values):
                logger.warning(f"Secret {key} contains suspicious default-like value")


# Create a singleton instance
_secrets_manager = None

def get_secrets_manager() -> SecretsManager:
    """
    Get the singleton SecretsManager instance.
    
    Returns:
        SecretsManager instance
    """
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager