"""
Secrets Manager Module

This module provides secure secrets management for the voice agent application.
It implements secure storage, retrieval, and encryption of sensitive configuration values.
"""

import os
import json
import logging
import base64
from typing import Dict, Any, Optional, Union
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecretsManager:
    """Secure secrets manager for handling sensitive configuration values."""
    
    def __init__(self, app_name: str = "voice_agent"):
        """
        Initialize the secrets manager.
        
        Args:
            app_name: Application name for namespacing secrets
        """
        self.app_name = app_name
        self.secrets_cache: Dict[str, Any] = {}
        self.encryption_key = self._get_or_create_encryption_key()
        self._load_secrets()
        
    def _get_or_create_encryption_key(self) -> bytes:
        """
        Get or create the encryption key.
        
        Returns:
            Encryption key bytes
        """
        # Get the master key from environment or generate one
        master_key = os.environ.get("SECRETS_MASTER_KEY")
        
        if not master_key:
            # In production, this should be set in the environment
            # For development, we'll use a default key (not secure for production)
            logger.warning("SECRETS_MASTER_KEY not found in environment. Using default key (NOT SECURE FOR PRODUCTION).")
            master_key = "default_development_key_not_for_production_use"
        
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
            
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a secret value.
        
        Args:
            key: Secret key
            default: Default value if key not found
            
        Returns:
            Secret value or default
        """
        # First check environment variables (highest priority)
        env_value = os.environ.get(key)
        if env_value is not None:
            return env_value
            
        # Then check the secrets cache
        return self.secrets_cache.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """
        Set a secret value.
        
        Args:
            key: Secret key
            value: Secret value
        """
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
            return ""


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